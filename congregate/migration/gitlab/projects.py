import json
from time import time
from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import get_dry_log, get_timedelta, json_pretty, remove_dupes, \
    is_error_message_present, safe_json_response, add_post_migration_stats, rotate_logs
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.groups import GroupsClient
from congregate.helpers.migrate_utils import get_dst_path_with_namespace, \
    get_full_path_with_parent_namespace, dig, get_staged_projects, get_staged_groups, find_user_by_email_comparison_without_id


class ProjectsClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.groups_api = GroupsApi()
        self.groups = GroupsClient()
        super().__init__()

    def get_projects(self):
        with open("{}/data/projects.json".format(self.app_path), "r") as f:
            return json.load(f)

    def root_user_present(self, members):
        for member in members:
            if member["id"] == self.config.import_user_id:
                return True
        return False

    def remove_import_user(self, pid):
        try:
            self.log.info("Removing import user (ID: {0}) from project (ID: {1})".format(
                self.config.import_user_id, pid))
            self.projects_api.remove_member(
                pid,
                self.config.import_user_id,
                self.config.destination_host,
                self.config.destination_token)
        except RequestException as re:
            self.log.error(
                "Failed to remove import user (ID: {0}) from project (ID: {1}), with error:\n{2}".format(self.config.import_user_id, pid, re))

    def retrieve_project_info(self, host, token):
        if self.config.src_parent_group_path:
            projects = self.groups_api.get_all_group_projects(
                self.config.src_parent_id, host, token, with_shared=False)
        else:
            projects = self.projects_api.get_all_projects(host, token)

        data = []
        for project in projects:
            if is_error_message_present(project):
                self.log.error(
                    "Failed to list project with response: {}".format(project))
            else:
                self.log.info(u"[ID: {0}] {1}: {2}".format(
                    project["id"], project["name"], project["description"]))
                project["members"] = [m for m in self.projects_api.get_members(
                    project["id"], host, token) if m["id"] != 1]
                data.append(project)

        with open("{}/data/projects.json".format(self.app_path), "w") as f:
            json.dump(remove_dupes(data), f, indent=4)
        return remove_dupes(data)

    def add_shared_groups(self, new_id, path, shared_with_groups):
        """Adds the list of groups we share the project with."""
        try:
            self.log.info(
                "Migrating project {} shared with groups".format(path))
            for group in shared_with_groups:
                dst_full_path = get_full_path_with_parent_namespace(
                    group["group_full_path"])
                new_gid = self.groups.find_group_id_by_path(
                    self.config.destination_host, self.config.destination_token, dst_full_path)
                if new_gid is not None:
                    data = {
                        "group_access": group["group_access_level"],
                        "group_id": new_gid,
                        "expires_at": group["expires_at"]
                    }
                    r = self.projects_api.add_shared_group(
                        self.config.destination_host, self.config.destination_token, new_id, data)
                    if r.status_code == 201:
                        self.log.info(
                            "Shared project {0} with group {1}".format(path, dst_full_path))
                    else:
                        self.log.error("Failed to share project {0} with group {1} due to:\n{2}".format(
                            path, dst_full_path, r.content))
            return True
        except RequestException as re:
            self.log.error("Failed to POST shared group {0} to project {1}, with error:\n{2}".format(
                dst_full_path, path, re))
            return False

    def find_project_by_path(self, host, token, dst_path_with_namespace):
        """Returns the project ID based on search by path."""
        self.log.info("Searching on {0} for project {1}".format(
            host, dst_path_with_namespace))
        resp = self.projects_api.get_project_by_path_with_namespace(
            dst_path_with_namespace, host, token)
        if resp.status_code == 200:
            project = safe_json_response(resp)
            if project and (project.get("path_with_namespace", '').lower() == dst_path_with_namespace.lower()):
                return project.get("id", None)
        return None

    def delete_projects(self, dry_run=True):
        staged_projects = get_staged_projects(self.app_path)
        for sp in staged_projects:
            # SaaS destination instances have a parent group
            path_with_namespace = get_dst_path_with_namespace(sp)
            self.log.info("Removing project {}".format(path_with_namespace))
            resp = self.projects_api.get_project_by_path_with_namespace(
                path_with_namespace,
                self.config.destination_host,
                self.config.destination_token)
            if resp is not None:
                if resp.status_code != 200:
                    self.log.info("Project {0} does not exist (status: {1})".format(
                        path_with_namespace, resp.status_code))
                elif not dry_run:
                    try:
                        project = resp.json()
                        if get_timedelta(project["created_at"]) < self.config.max_asset_expiration_time:
                            self.projects_api.delete_project(
                                self.config.destination_host,
                                self.config.destination_token,
                                project["id"])
                        else:
                            self.log.info("Ignoring {0}. Project existed before {1} hours".format(
                                project["name_with_namespace"], self.config.max_asset_expiration_time))
                    except RequestException as re:
                        self.log.error(
                            "Failed to remove project\n{0}\nwith error:\n{1}".format(json_pretty(sp), re))
            else:
                self.log.error(
                    "Failed to GET project {} by path_with_namespace".format(path_with_namespace))

    def count_unarchived_projects(self):
        unarchived_user_projects = []
        unarchived_group_projects = []
        for project in self.projects_api.get_all_projects(self.config.source_host, self.config.source_token):
            if not project.get("archived", True):
                unarchived_user_projects.append(project["path_with_namespace"]) if project["namespace"][
                    "kind"] == "user" else unarchived_group_projects.append(project["path_with_namespace"])
        self.log.info("Unarchived user projects ({0}):\n{1}".format(
            len(unarchived_user_projects), "\n".join(up for up in unarchived_user_projects)))
        self.log.info("Unarchived group projects ({0}):\n{1}".format(
            len(unarchived_group_projects), "\n".join(up for up in unarchived_group_projects)))

    def archive_staged_projects(self, dry_run=True):
        start = time()
        rotate_logs()
        staged_projects = get_staged_projects(self.app_path)
        self.log.info("Project count is: {}".format(len(staged_projects)))
        try:
            for project in staged_projects:
                self.log.info("{0}Archiving source project {1}".format(
                    get_dry_log(dry_run),
                    project["path_with_namespace"]))
                if not dry_run:
                    self.projects_api.archive_project(
                        self.config.source_host,
                        self.config.source_token,
                        project["id"])
        except RequestException as re:
            self.log.error(
                "Failed to archive staged projects, with error:\n{}".format(re))
        finally:
            add_post_migration_stats(start, log=self.log)

    def unarchive_staged_projects(self, dry_run=True):
        start = time()
        rotate_logs()
        staged_projects = get_staged_projects(self.app_path)
        self.log.info("Project count is: {}".format(len(staged_projects)))
        try:
            for project in staged_projects:
                self.log.info("{0}Unarchiving source project {1}".format(
                    get_dry_log(dry_run),
                    project["path_with_namespace"]))
                if not dry_run:
                    self.projects_api.unarchive_project(
                        self.config.source_host,
                        self.config.source_token,
                        project["id"])
        except RequestException as re:
            self.log.error(
                "Failed to unarchive staged projects, with error:\n{}".format(re))
        finally:
            add_post_migration_stats(start, log=self.log)

    def find_unimported_projects(self, dry_run=True):
        unimported_projects = []
        files = self.get_projects()
        if files is not None and files:
            for project in files:
                try:
                    path = project["path_with_namespace"]
                    self.log.info(
                        "Searching for project {} on destination".format(path))
                    project_exists = False
                    for proj in self.projects_api.search_for_project(
                            self.config.destination_host,
                            self.config.destination_token,
                            project['name']):
                        if proj["name"] == project["name"]:
                            if dig(project, 'namespace', 'full_path', default="").lower() == proj.get("path_with_namespace", "").lower():
                                project_exists = True
                                break
                    if not project_exists:
                        self.log.info("Adding project {}".format(path))
                        unimported_projects.append(
                            "%s/%s" % (project["namespace"], project["name"]))
                except IOError as ioe:
                    self.log.error(
                        "Failed to find unimported projects, with error:\n{}".format(ioe))

        if unimported_projects is not None and unimported_projects:
            self.log.info("{0}Found {1} unimported projects".format(
                get_dry_log(dry_run),
                len(unimported_projects)))
            if not dry_run:
                with open("{}/data/unimported_projects.txt".format(self.app_path), "w") as f:
                    for project in unimported_projects:
                        f.writelines(project + "\n")

    def find_empty_repos(self):
        empty_repos = []
        dest_projects = self.projects_api.get_all_projects(
            self.config.destination_host,
            self.config.destination_token,
            statistics=True)
        src_projects = self.projects_api.get_all_projects(
            self.config.source_host,
            self.config.source_token,
            statistics=True)
        for dp in dest_projects:
            if dp.get("statistics", None) is not None and dig(dp, 'statistics', 'repository_size', default=-1) == 0:
                self.log.info("Found empty repo on destination instance: {}".format(
                    dp["name_with_namespace"]))
                for sp in src_projects:
                    if sp["name"] == dp["name"] and dig(dp, 'namespace', 'path') in dig(sp, 'namespace', 'path', default=""):
                        self.log.info("Found source project {}".format(
                            sp["name_with_namespace"]))
                        if sp.get("statistics", None) is not None and dig(sp, 'statistics', 'repository_size', default=-1) == 0:
                            self.log.info(
                                "Project is empty in source instance. Ignoring")
                        else:
                            empty_repos.append(dp["name_with_namespace"])
        self.log.info("Empty repositories ({0}):\n{1}".format(
            len(empty_repos), "\n".join(ep for ep in empty_repos)))

    def validate_staged_projects_schema(self):
        staged_groups = get_staged_groups(self.app_path)
        for g in staged_groups:
            self.log.info(g)
            if g.get("name", None) is None:
                self.log.warning("name is missing")
            if g.get("namespace", None) is None:
                self.log.warning("namespace is missing")
            if g.get("project_type", None) is None:
                self.log.warning("project_type is missing")
            if g.get("default_branch", None) is None:
                self.log.warning("default_branch is missing")
            if g.get("visibility", None) is None:
                self.log.warning("visibility is missing")
            if g.get("http_url_to_repo", None) is None:
                self.log.warning("http_url_to_repo is missing")
            if g.get("shared_runners_enabled", None) is None:
                self.log.warning("shared_runners_enabled is missing")
            if g.get("members", None) is None:
                self.log.warning("members is missing")
            if g.get("id", None) is None:
                self.log.warning("id is missing")
            if g.get("description", None) is None:
                self.log.warning("description is missing")

    def add_members_to_destination_project(self, host, token, project_id, members):
        result = {}
        self.log.info(
            f"Adding members to project ID {project_id}:\n{json_pretty(members)}")
        for member in members:
            user_id_req = find_user_by_email_comparison_without_id(
                member["email"])
            member["user_id"] = user_id_req.get(
                "id", None) if user_id_req else None
            result[member["email"]] = False
            if member.get("user_id"):
                resp = safe_json_response(self.projects_api.add_member(
                    project_id, host, token, member))
                if resp:
                    result[member["email"]] = True
        return result
