import json
from urllib import quote_plus
from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import get_dry_log
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.helpers.migrate_utils import get_project_namespace, is_user_project, get_user_project_namespace, get_timedelta


class ProjectsClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.groups_api = GroupsApi()
        super(ProjectsClient, self).__init__()

    @staticmethod
    def get_full_namespace_path(namespace_prefix, namespace, project_name):
        if len(namespace_prefix) > 0:
            return namespace_prefix + "/" + namespace + "/" + project_name
        return namespace + "/" + project_name

    def get_projects(self):
        with open("{}/data/project_json.json".format(self.app_path), "r") as f:
            return json.load(f)

    def get_staged_projects(self):
        with open("{}/data/stage.json".format(self.app_path), "r") as f:
            return json.load(f)

    def search_for_project_with_namespace_path(self, host, token, namespace_prefix, namespace, project_name):
        url_encoded_path = quote_plus(self.get_full_namespace_path(
            namespace_prefix, namespace, project_name))
        resp = self.projects_api.get_project_by_path_with_namespace(
            url_encoded_path, host, token)
        if resp.status_code == 200:
            return resp.json()
        return None

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
        except RequestException, e:
            self.log.error(
                "Failed to remove import user (ID: {0}) from project (ID: {1}), with error:\n{2}".format(self.config.import_user_id, pid, e))

    def add_shared_groups(self, old_id, new_id):
        """Adds the list of groups we share the project with."""
        old_project = self.projects_api.get_project(
            old_id, self.config.source_host, self.config.source_token).json()
        project_name = old_project["name"]
        for group in old_project["shared_with_groups"]:
            path = group["group_full_path"]
            name = group["group_name"]
            new_group_id = self.get_new_group_id(name, path)
            if new_group_id is not None:
                data = {
                    "group_access": group["group_access_level"],
                    "group_id": new_group_id,
                    "expires_at": group["expires_at"]
                }
                try:
                    r = self.projects_api.add_shared_group(
                        self.config.destination_host, self.config.destination_token, new_id, data)
                    if r.status_code == 201:
                        self.log.info(
                            "Shared project {0} with group {1}".format(project_name, name))
                    else:
                        self.log.warn("Failed to share project {0} with group {1} due to:\n{2}".format(
                            project_name, name, r.content))
                except RequestException, e:
                    self.log.error("Failed to POST shared group {0} to project {1}, with error:\n{2}".format(
                        name, project_name, e))

    def get_new_group_id(self, name, path):
        """Returns the group's ID on the destination instance."""
        try:
            groups = self.groups_api.search_for_group(
                name, self.config.destination_host, self.config.destination_token)
            if groups:
                for group in groups:
                    if group["full_path"] == path:
                        return group["id"]
            else:
                self.log.warn(
                    "Shared group {} does not exist or is not yet imported".format(path))
        except RequestException, e:
            self.log.error(
                "Failed to GET group {0} ID, with error:\n{1}".format(name, e))

    def __old_project_avatar(self, id):
        """Returns the source project avatar."""
        old_project = self.projects_api.get_project(
            id, self.config.source_host, self.config.source_token).json()
        return old_project["avatar_url"]

    def find_project_by_path(self, host, token, full_parent_namespace, namespace, name):
        """Returns a tuple (project_exists, ID) based on path."""
        project = self.search_for_project_with_namespace_path(
            host, token, full_parent_namespace, namespace, name)
        if project is not None:
            if project.get("path_with_namespace", None) is not None:
                if project["path_with_namespace"] == self.get_full_namespace_path(full_parent_namespace, namespace, name):
                    self.log.info("SKIP: Project {} already exists".format(
                        project["path_with_namespace"]))
                    return True, project["id"]
        return False, None

    def delete_projects(self, dry_run=True):
        staged_projects = self.get_staged_projects()
        for sp in staged_projects:
            # SaaS destination instances have a parent group
            path_with_namespace = "{0}/{1}".format(get_user_project_namespace(sp) if is_user_project(
                sp) else get_project_namespace(sp), sp["name"].replace(" ", "-"))
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
                            self.log("Ignoring %s. Project existed before %d hours" % (project["name_with_namespace"], self.config.max_asset_expiration_time))
                    except RequestException, e:
                        self.log.error(
                            "Failed to remove project {0}\nwith error: {1}".format(sp, e))
            else:
                self.log.error(
                    "Failed to GET project {} by path_with_namespace".format(path_with_namespace))

    def count_unarchived_projects(self):
        unarchived_projects = []
        for project in self.projects_api.get_all_projects(self.config.source_host, self.config.source_token):
            if project.get("archived", None) is not None:
                if not project["archived"]:
                    unarchived_projects.append(project["name_with_namespace"])
        self.log.info("Unarchived projects ({0}):\n{1}".format(
            len(unarchived_projects), "\n".join(up for up in unarchived_projects)))

    def archive_staged_projects(self, dry_run=True):
        staged_projects = self.get_staged_projects()
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
        except RequestException, e:
            self.log.error(
                "Failed to archive staged projects, with error:\n{}".format(e))

    def unarchive_staged_projects(self, dry_run=True):
        staged_projects = self.get_staged_projects()
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
        except RequestException, e:
            self.log.error(
                "Failed to unarchive staged projects, with error:\n{}".format(e))

    def find_unimported_projects(self, dry_run=True):
        unimported_projects = []
        files = self.get_projects()
        if files is not None and files:
            for project_json in files:
                try:
                    path = project_json["path_with_namespace"]
                    self.log.info(
                        "Searching for project {} on destination".format(path))
                    project_exists = False
                    for proj in self.projects_api.search_for_project(
                            self.config.destination_host,
                            self.config.destination_token,
                            project_json['name']):
                        if proj["name"] == project_json["name"]:
                            if project_json["namespace"]["full_path"].lower() == proj["path_with_namespace"].lower():
                                project_exists = True
                                break
                    if not project_exists:
                        self.log.info("Adding project {}".format(path))
                        unimported_projects.append(
                            "%s/%s" % (project_json["namespace"], project_json["name"]))
                except IOError, e:
                    self.log.error(
                        "Failed to find unimported projects, with error:\n{}".format(e))

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
            if dp.get("statistics", None) is not None and dp["statistics"]["repository_size"] == 0:
                self.log.info("Found empty repo on destination instance: {}".format(
                    dp["name_with_namespace"]))
                for sp in src_projects:
                    if sp["name"] == dp["name"] and dp["namespace"]["path"] in sp["namespace"]["path"]:
                        self.log.info("Found source project {}".format(
                            sp["name_with_namespace"]))
                        if sp.get("statistics", None) is not None and sp["statistics"]["repository_size"] == 0:
                            self.log.info(
                                "Project is empty in source instance. Ignoring")
                        else:
                            empty_repos.append(dp["name_with_namespace"])
        self.log.info("Empty repositories ({0}):\n{1}".format(
            len(empty_repos), "\n".join(ep for ep in empty_repos)))

    def validate_staged_projects_schema(self):
        with open("%s/data/staged_groups.json" % self.app_path, "r") as f:
            staged_groups = json.load(f)
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
