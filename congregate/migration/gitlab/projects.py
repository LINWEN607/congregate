import json
import base64
import datetime
from time import time
from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import get_dry_log, get_timedelta, \
    is_error_message_present, safe_json_response, strip_protocol, \
    get_decoded_string_from_b64_response_content, do_yml_sub
from congregate.helpers.json_utils import json_pretty, read_json_file_into_object
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.processes import start_multi_process_stream_with_args
from congregate.helpers.migrate_utils import get_dst_path_with_namespace, \
    get_full_path_with_parent_namespace, dig, get_staged_projects, get_staged_groups, find_user_by_email_comparison_without_id, add_post_migration_stats
from congregate.helpers.utils import rotate_logs
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi


class ProjectsClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.groups_api = GroupsApi()
        self.groups = GroupsClient()
        self.users = UsersClient()
        self.project_repository_api = ProjectRepositoryApi()
        super().__init__()

    def get_projects(self):
        with open("{}/data/projects.json".format(self.app_path), "r") as f:
            return json.load(f)

    def connect_to_mongo(self):
        return MongoConnector()

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

    def retrieve_project_info(self, host, token, processes=None):
        if self.config.src_parent_group_path:
            start_multi_process_stream_with_args(
                self.handle_retrieving_project,
                self.groups_api.get_all_group_projects(
                    self.config.src_parent_id, host, token, with_shared=False),
                host,
                token,
                processes=processes)
        else:
            start_multi_process_stream_with_args(
                self.handle_retrieving_project,
                self.projects_api.get_all_projects(host, token),
                host,
                token,
                processes=processes)

    def handle_retrieving_project(self, host, token, project, mongo=None):
        if not mongo:
            mongo = self.connect_to_mongo()

        if is_error_message_present(project):
            self.log.error(
                "Failed to list project with response: {}".format(project))
        else:
            self.log.info(u"[ID: {0}] {1}: {2}".format(
                project["id"], project["name"], project["description"]))
            project["members"] = [m for m in self.projects_api.get_members(
                project["id"], host, token) if m["id"] != 1]

            mongo.insert_data(f"projects-{strip_protocol(host)}", project)
        mongo.close_connection()

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
            if project and (project.get("path_with_namespace",
                                        '').lower() == dst_path_with_namespace.lower()):
                return project.get("id", None)
        return None

    def delete_projects(self, dry_run=True):
        staged_projects = get_staged_projects()
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
                        if get_timedelta(
                                project["created_at"]) < self.config.max_asset_expiration_time:
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
        for project in self.projects_api.get_all_projects(
                self.config.source_host, self.config.source_token):
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
        staged_projects = get_staged_projects()
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
        staged_projects = get_staged_projects()
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
                            if dig(project, 'namespace', 'full_path', default="").lower(
                            ) == proj.get("path_with_namespace", "").lower():
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
            if dp.get("statistics", None) is not None and dig(
                    dp, 'statistics', 'repository_size', default=-1) == 0:
                self.log.info("Found empty repo on destination instance: {}".format(
                    dp["name_with_namespace"]))
                for sp in src_projects:
                    if sp["name"] == dp["name"] and dig(dp, 'namespace', 'path') in dig(
                            sp, 'namespace', 'path', default=""):
                        self.log.info("Found source project {}".format(
                            sp["name_with_namespace"]))
                        if sp.get("statistics", None) is not None and dig(
                                sp, 'statistics', 'repository_size', default=-1) == 0:
                            self.log.info(
                                "Project is empty in source instance. Ignoring")
                        else:
                            empty_repos.append(dp["name_with_namespace"])
        self.log.info("Empty repositories ({0}):\n{1}".format(
            len(empty_repos), "\n".join(ep for ep in empty_repos)))

    def validate_staged_projects_schema(self):
        staged_groups = get_staged_groups()
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

    def add_members_to_destination_project(
            self, host, token, project_id, members):
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

    def get_replacement_data(self, data, f, project_id, src_branch):
        """
        :param data: (dict) Data for the replacement task. See form in description
        :param f: (str) The filename we are replacing for. Used for logging in this method
        :param project_id: (int) The project id on the destination
        :param src_branch: (str) The name of the branch we will be pulling files from in the project

        Takes a pattern replace list data item of form:
        'data':
            {
                'pattern': regex pattern string,
                'replace_with': replacement string. can be a ci_var name
            }
        checks pattern and replace_with are valid, and returns them as a tuple. Does the logging on invalid values
        """
        if not data or not isinstance(data, dict) or len(data) == 0:
            self.log.warning(
                f"No replacement data configured for file {f} in project_id {project_id} branch {src_branch}"
            )
            return None
        pattern = data.get("pattern", None)
        if not pattern or not isinstance(
                pattern, str) or pattern.strip() == "":
            self.log.warning(
                f"No pattern configured for file {f} in project_id {project_id} branch {src_branch}"
            )
            return None
        replace_with = data.get("replace_with", None)
        if not replace_with or not isinstance(
                replace_with, str) or replace_with.strip() == "":
            self.log.warning(
                f"No replace_with configured for file {f} in project_id {project_id} branch {src_branch}"
            )
            return None
        return pattern, replace_with

    def migrate_gitlab_variable_replace_ci_yml(self, project_id):
        """
        :param project_id: (int) The project_id at the destination

        Does the pattern replacement in project files, and cuts a branch with the changes
        {
            "filenames": [
                ".gitlab-ci.yml",
                "requirements.yml",
                "ansible/playbooks/requirements.yml",
                "ansible/molecule/default/requirements.yml"
            ],
            "patterns": [
                {
                    "pattern": "https://git.internal.ca/ansible/roles/global-setup.git",
                    "replace_with": "https://gitlab.com/company/infra/ansible/roles/global-setup.git"
                },
                {
                    "pattern": "https://git.internal.ca/ansible/roles/healthcheck.git",
                    "replace_with": "https://gitlab.com/company/infra/ansible/roles/healthcheck.git"
                },
                {...}
            ]
        }
        Notes:
        * Single branch per project, with commits per configured file.
        * Does not group same file names, so if a file is listed twice, instead of once with multiple data entries, it will get two commits on the same new branch.
          * Since the initial read is *always* from the default, this means that the last listed change will "win"
        """
        self.log.info(
            f"Performing URL remapping for destination project id {project_id}")

        create_branch = False
        branch_name = ""
        yml_file = ""
        new_yml_64 = ""

        pattern_list = read_json_file_into_object(
            self.config.remapping_file_path
        )

        # Get the project from destination to get the default branch
        dstn_project = self.projects_api.get_project(
            project_id,
            self.config.destination_host,
            self.config.destination_token
        )

        if dstn_project and dstn_project.status_code == 200:
            dstn_project_json = safe_json_response(dstn_project)
            src_branch = dstn_project_json.get("default_branch", None)
            self.log.info(f"Source branch is {src_branch}")
            if not src_branch or src_branch.strip() == "":
                self.log.warning(
                    f"Could not determine default branch for project_id {project_id}"
                )
                return
        
        # Get the list of filenames
        filenames = pattern_list.get("filenames", None)
        if not filenames:
            self.log.error(
                "No URL replacement filenames found"
            )
            return

        # Get the list of patterns
        patterns = pattern_list.get("patterns", None)
        if not patterns:
            self.log.error(
                "No URL replacement patterns found"
            )
            return

        for f in filenames:
            if f == "":
                self.log.warning(
                    f"Empty filename in replacement configuration for project_id {project_id} branch {src_branch}"
                )
                continue
            repo_file = f"{f}?ref={src_branch}"
            self.log.info(f"Pulling repository file for rewrite: {repo_file}")
            yml_file_response = self.project_repository_api.get_single_repo_file(
                self.config.destination_host,
                self.config.destination_token,
                project_id,
                f,
                src_branch
            )

            # Content is base64 string
            if yml_file_response is None or (
                    yml_file_response is not None and yml_file_response.status_code != 200):
                self.log.warning(
                    f"No {f} file available for project_id {project_id} branch {src_branch}"
                )
                continue

            if yml_file_response.status_code == 200:
                yml_file = get_decoded_string_from_b64_response_content(
                    yml_file_response
                )
                if not yml_file or yml_file.strip() == "":
                    self.log.warning(
                        f"Empty {f} file found for project_id {project_id} branch {src_branch}"
                    )
                    continue
            elif yml_file_response.status_code == 404:
                self.log.warning(
                    f"No {f} file available for project_id {project_id} branch {src_branch}"
                )
                continue

            # We have the decoded base64
            # Loop of the patterns list
            for p in patterns:
                repl_data = self.get_replacement_data(
                    p, f, project_id, src_branch
                )

                if not repl_data:
                    self.log.warning(
                        f"No replacement data configured for file {f} in project_id {project_id} branch {src_branch}"
                    )
                    continue
                pattern = repl_data[0]
                replace_with = repl_data[1]

                # Perform the substitution
                self.log.info(f"Subbing {pattern} with {replace_with} in {f}")
                subs = do_yml_sub(yml_file, pattern, replace_with)

                # If nothing changed, skip it all
                if subs[1] == 0:
                    self.log.info(
                        f"Found no instances of {pattern} in project_id {project_id} branch {src_branch}"
                    )
                    continue

                #  Log info
                self.log.info(
                    f"Replaced {subs[1]} instances of {pattern} with {replace_with} on project_id {project_id}"
                )
                create_branch = True
                # Make the next pass of the file be with the current subbed
                # value
                yml_file = subs[0]

            # After changing all the data, encode and write
            # b64encode the new data. Must also encode the subs results. This
            # returns a byte object b''
            new_yml_64 = base64.b64encode(yml_file.encode())
            # Put it back to string for the eventual post
            new_yml_64 = new_yml_64.decode()

            # Don't want to create a branch unless we find something to do, and haven't already created one
            # (the name check). For now, place everything on one branch
            # If we want multiple branches, reset create to False *and* empty
            # name
            if create_branch and branch_name == "":
                # Create a branch
                n = datetime.datetime.now()
                branch_name = f"ci-rewrite-{n.year}{n.month}{n.day}{n.hour}{n.minute}{n.second}"
                self.log.info(
                    f"Creating branch {branch_name} in project {project_id} from {src_branch}")
                branch_data = {
                    "branch": branch_name,
                    "ref": src_branch
                }
                branch_create_resp = self.projects_api.create_branch(
                    self.config.destination_host,
                    self.config.destination_token,
                    project_id,
                    data=json.dumps(branch_data)
                )
                if not branch_create_resp or (
                        branch_create_resp and branch_create_resp.status_code not in (200, 201)):
                    self.log.error(
                        f"Could not create branch for regex replace:\nproject: {project_id}\nbranch data: {branch_data}")
                else:
                    create_branch = False

            if branch_name != "":
                # Put the new file
                put_file_data = {
                    "branch": f"{branch_name}",
                    "content": f"{new_yml_64}",
                    "encoding": "base64",
                    "commit_message": f"Commit for migration regex replace replacing file {f}"
                }
                put_resp = self.project_repository_api.put_single_repo_file(
                    self.config.destination_host,
                    self.config.destination_token,
                    project_id,
                    f"{f}",
                    put_file_data
                )
                if not put_resp or (put_resp and put_resp.status_code == 400):
                    self.log.error(f"Could not put commit for regex replace:\nproject: {project_id}\nbranch name: {branch_name}\nfile: {f}")
                branch_name = ""

            # A branch_name reset would need to go here for the multiple
            # branches
