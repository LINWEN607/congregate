import json
import base64
from os.path import dirname
import datetime
from sqlite3 import DataError
from time import time, sleep
from requests.exceptions import RequestException
from tqdm import tqdm
from celery import shared_task

from gitlab_ps_utils.misc_utils import get_dry_log, get_timedelta, \
    is_error_message_present, safe_json_response, strip_netloc, \
    get_decoded_string_from_b64_response_content, do_yml_sub, strip_scheme
from gitlab_ps_utils.json_utils import json_pretty, read_json_file_into_object, write_json_to_file
from gitlab_ps_utils.list_utils import remove_dupes
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import mongo_connection, CongregateMongoConnector
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.contributor_retention import ContributorRetentionClient
from congregate.migration.gitlab import constants
from congregate.migration.mirror import MirrorClient
from congregate.helpers.migrate_utils import get_dst_path_with_namespace,  get_full_path_with_parent_namespace, \
    dig, get_staged_projects, get_staged_groups, find_user_by_email_comparison_without_id, add_post_migration_stats, is_user_project, \
    check_for_staged_user_projects, get_stage_wave_paths
from congregate.helpers.utils import rotate_logs
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.migration.meta.api_models.shared_with_group import SharedWithGroupPayload


class ProjectsClient(BaseClass):
    def __init__(self, DRY_RUN=True):
        self.projects_api = ProjectsApi()
        self.groups_api = GroupsApi()
        self.users_api = UsersApi()
        self.groups = GroupsClient()
        self.users = UsersClient()
        self.mirror = MirrorClient()
        self.project_repository_api = ProjectRepositoryApi()
        self.dry_run = DRY_RUN
        self.skip_project_members = False
        super().__init__()

    def get_projects(self):
        with open(f"{self.app_path}/data/projects.json", "r") as f:
            return json.load(f)

    def root_user_present(self, members):
        for member in members:
            if member["id"] == self.config.import_user_id:
                return True
        return False

    def retrieve_project_info(self, host, token, processes=None):
        if self.config.direct_transfer:
            for project in self.projects_api.get_all_projects(host, token):
                handle_retrieving_project.delay(host, token, project)
        else:
            if self.config.src_parent_group_path:
                self.multi.start_multi_process_stream_with_args(
                    self.handle_retrieving_project,
                    self.groups_api.get_all_group_projects(
                        self.config.src_parent_id, host, token, include_subgroups=True),
                    host,
                    token,
                    processes=processes)
            else:
                self.multi.start_multi_process_stream_with_args(
                    self.handle_retrieving_project,
                    self.projects_api.get_all_projects(host, token),
                    host,
                    token,
                    processes=processes)

    def handle_retrieving_project(self, host, token, project, mongo=None):
        if not mongo:
            mongo = CongregateMongoConnector()
        error, project = is_error_message_present(project)
        if error or not project:
            self.log.error(f"Failed to list project:\n{project}")
        else:
            for k in constants.PROJECT_KEYS_TO_IGNORE:
                project.pop(k, None)
            project["members"] = [] if self.skip_project_members else list(
                self.projects_api.get_members(project["id"], host, token))
            mongo.insert_data(f"projects-{strip_netloc(host)}", project)
        mongo.close_connection()

    def add_shared_groups(self, new_id, path, shared_with_groups):
        """Adds the list of groups we share the project with."""
        try:
            self.log.info(f"Migrating project {path} shared with groups")
            for group in shared_with_groups:
                dst_full_path = get_full_path_with_parent_namespace(
                    group["group_full_path"])
                new_gid = self.groups.find_group_id_by_path(
                    self.config.destination_host, self.config.destination_token, dst_full_path)
                if new_gid:
                    data = SharedWithGroupPayload(
                        group_access=group["group_access_level"],
                        group_id=new_gid,
                        expires_at=group["expires_at"]
                    )
                    r = self.projects_api.add_shared_group(
                        self.config.destination_host, self.config.destination_token, new_id, data.to_dict())
                    if r.status_code == 201:
                        self.log.info(
                            f"Shared project '{path}' with group '{dst_full_path}'")
                    # 409 being already shared
                    elif r.status_code not in [201, 409]:
                        self.log.error(
                            f"Failed to share project '{path}' with group '{dst_full_path}', using payload\n{data} due to:\n{r} - {r.text}")
                else:
                    self.log.error(
                        f"Failed to find project '{path}' shared group '{dst_full_path}' on destination using new ID {new_gid}")
            return True
        except RequestException as re:
            self.log.error(
                f"Failed to POST shared group '{dst_full_path}' to project '{path}', with error:\n{re}")
            return False

    def find_project_by_path(self, host, token, dst_path_with_namespace):
        """Returns the project ID based on search by path."""
        self.log.info(
            f"Searching on {host} for project {dst_path_with_namespace}")
        resp = self.projects_api.get_project_by_path_with_namespace(
            dst_path_with_namespace, host, token)
        if resp.status_code == 200:
            project = safe_json_response(resp)
            if project and (project.get("path_with_namespace",
                                        '').lower() == dst_path_with_namespace.lower()):
                return project.get("id")
        return None

    def delete_projects(self, dry_run=True, permanent=False):
        staged_projects = get_staged_projects()
        for sp in tqdm(staged_projects, total=len(staged_projects), colour=self.TANUKI, desc=self.DESC, unit=self.UNIT):
            # GitLab.com destination instances have a parent group
            path_with_namespace, _ = get_stage_wave_paths(sp)
            self.log.info(
                f"{get_dry_log(dry_run)}Deleting project '{path_with_namespace}' on destination")
            try:
                resp = self.projects_api.get_project_by_path_with_namespace(
                    path_with_namespace, self.config.destination_host, self.config.destination_token)
                if resp.status_code != 200:
                    self.log.warning(
                        f"Project '{path_with_namespace}' does not exist: {resp} - {resp.text})")
                elif not dry_run:
                    self.delete_project(
                        resp, path_with_namespace, permanent=permanent)
            except RequestException as re:
                self.log.error(
                    f"Failed to delete project '{path_with_namespace}' on destination:\n{re}")

    def delete_project(self, resp, path_with_namespace, permanent=False):
        host = self.config.destination_host
        token = self.config.destination_token
        exp_time = self.config.max_asset_expiration_time
        project = safe_json_response(resp)
        if get_timedelta(project.get("created_at", exp_time)) < exp_time:
            pid = project["id"]
            resp = self.projects_api.delete_project(host, token, pid)
            if resp.status_code not in [200, 202, 204]:
                self.log.error(
                    f"Failed to delete project '{path_with_namespace}' on destination:\n{resp} - {resp.text}")
            elif permanent:
                if deleted_path_json := safe_json_response(self.projects_api.get_project(pid, host, token)):
                    # Allow time for project to rename and archive as part of soft deletion
                    sleep(5)
                    resp = self.projects_api.delete_project(host, token, pid, full_path=deleted_path_json.get(
                        "path_with_namespace"), permanent=permanent)
                    if resp.status_code not in [200, 202, 204]:
                        self.log.error(
                            f"Failed to permanently delete project '{path_with_namespace}' on destination:\n{resp} - {resp.text}")
        else:
            self.log.warning(
                f"SKIP: project '{path_with_namespace}' was created {exp_time} hours ago")

    def count_unarchived_projects(self, local=False):
        unarchived_user_projects = []
        unarchived_group_projects = []
        for project in (self.get_projects() if local else self.projects_api.get_all_projects(
                self.config.source_host, self.config.source_token)):
            if not project.get("archived", True):
                unarchived_user_projects.append(project["path_with_namespace"]) if project["namespace"][
                    "kind"] == "user" else unarchived_group_projects.append(project["path_with_namespace"])
        self.log.info("Unarchived user projects ({0}):\n{1}".format(
            len(unarchived_user_projects), "\n".join(up for up in unarchived_user_projects)))
        self.log.info("Unarchived group projects ({0}):\n{1}".format(
            len(unarchived_group_projects), "\n".join(up for up in unarchived_group_projects)))

    def update_staged_projects_archive_state(
            self, archive=True, dest=False, dry_run=True, rollback=False):
        start = time()
        rotate_logs()
        staged_projects = get_staged_projects()
        host = self.config.destination_host if dest else self.config.source_host
        token = self.config.destination_token if dest else self.config.source_token
        host_type = "destination" if dest else "source"
        action_type = "Archive" if archive else "Unarchive"
        self.log.info(f"Project count: {len(staged_projects)}")
        try:
            for sp in tqdm(staged_projects, total=len(staged_projects), colour=self.TANUKI, desc=self.DESC, unit=self.UNIT):
                # Get source/destination project full path and ID
                path = get_dst_path_with_namespace(
                    sp) if dest else sp["path_with_namespace"]
                pid = self.find_project_by_path(
                    host, token, path) if dest else sp["id"]
                self.log.info(
                    f"{get_dry_log(dry_run)}{action_type} {host_type} ({host}) project {path}")
                if not dry_run:
                    if archive:
                        resp = self.projects_api.archive_project(
                            host, token, pid)
                        if resp.status_code != 201:
                            self.log.error(
                                f"Failed to {action_type.lower()} {host_type} ({host}) project {path}, with response:\n{resp} - {resp.text}")
                    else:
                        # Unarchive only previously active projects during rollback
                        if rollback and not sp["archived"]:
                            if self.config.archive_logic:
                                self.log.info(
                                    f"Unarchiving previously active project '{path}' (ID: {pid})")
                                resp = self.projects_api.unarchive_project(
                                    host, token, pid)
                                if resp.status_code != 201:
                                    self.log.error(
                                        f"Failed to {action_type.lower()} {host_type} ({host}) project {path}, with response:\n{resp} - {resp.text}")
                        elif not rollback:
                            resp = self.projects_api.unarchive_project(
                                host, token, pid)
                            if resp.status_code != 201:
                                self.log.error(
                                    f"Failed to {action_type.lower()} {host_type} ({host}) project {path}, with response:\n{resp} - {resp.text}")
        except RequestException as re:
            self.log.error(
                f"Failed to {action_type.lower()} {host_type} ({host}) projects, with error:\n{re}")
        finally:
            add_post_migration_stats(start, log=self.log)

    def filter_projects_by_state(self, archived=False, dry_run=True):
        staged = get_staged_projects()
        self.log.info(f"Total staged projects count: {len(staged)}")
        arch = [s for s in staged if s.get("archived")]
        unarch = [s for s in staged if not s.get("archived")]
        diff = arch if archived else unarch

        self.log.info(
            f"{get_dry_log(dry_run)}Keeping ONLY {'archived' if archived else 'unarchived'} {len(diff)}/{len(staged)} projects staged")
        if not dry_run:
            write_json_to_file(
                f"{self.app_path}/data/staged_projects.json", diff, log=self.log)
        return len(diff)

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
            if g.get("name") is None:
                self.log.warning("name is missing")
            if g.get("namespace") is None:
                self.log.warning("namespace is missing")
            if g.get("project_type") is None:
                self.log.warning("project_type is missing")
            if g.get("default_branch") is None:
                self.log.warning("default_branch is missing")
            if g.get("visibility") is None:
                self.log.warning("visibility is missing")
            if g.get("http_url_to_repo") is None:
                self.log.warning("http_url_to_repo is missing")
            if g.get("shared_runners_enabled") is None:
                self.log.warning("shared_runners_enabled is missing")
            if g.get("members") is None:
                self.log.warning("members is missing")
            if g.get("id") is None:
                self.log.warning("id is missing")
            if g.get("description") is None:
                self.log.warning("description is missing")

    def add_members_to_destination_project(
            self, host, token, project_id, members):
        result = {}
        self.log.info(
            f"Adding members to project ID {project_id}:\n{json_pretty(members)}")
        for member in members:
            user_id_req = find_user_by_email_comparison_without_id(
                member["email"])
            member["user_id"] = user_id_req.get("id") if user_id_req else None
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
                    f"No '{f}' file available for project_id {project_id} branch '{src_branch}'"
                )
                continue

            if yml_file_response.status_code == 200:
                yml_file = get_decoded_string_from_b64_response_content(
                    yml_file_response
                )
                if not yml_file or yml_file.strip() == "":
                    self.log.warning(
                        f"Empty '{f}' file found for project_id {project_id} branch '{src_branch}'"
                    )
                    continue
            elif yml_file_response.status_code == 404:
                self.log.warning(
                    f"No '{f}' file available for project_id {project_id} branch '{src_branch}'"
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
                        f"No replacement data configured for file '{f}' in project_id {project_id} branch '{src_branch}'"
                    )
                    continue
                pattern = repl_data[0]
                replace_with = repl_data[1]

                # Perform the substitution
                self.log.info(
                    f"Subbing '{pattern}' with '{replace_with}' in file '{f}'")
                subs = do_yml_sub(yml_file, pattern, replace_with)

                # If nothing changed, skip it all
                if subs[1] == 0:
                    self.log.info(
                        f"Found no instances of '{pattern}' in project_id {project_id} branch '{src_branch}'"
                    )
                    continue

                #  Log info
                self.log.info(
                    f"Replaced {subs[1]} instances of '{pattern}' with '{replace_with}' on project_id {project_id}"
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
                    f"Creating branch '{branch_name}' in project {project_id} from '{src_branch}'")
                branch_data = {
                    "branch": branch_name,
                    "ref": src_branch
                }
                branch_create_resp = self.projects_api.create_branch(
                    self.config.destination_host,
                    self.config.destination_token,
                    project_id,
                    data=branch_data
                )
                if not branch_create_resp or (
                        branch_create_resp and branch_create_resp.status_code != 201):
                    self.log.error(
                        f"Could not create branch `{branch_name}' for regex replace:\nproject: {project_id}\nbranch data: {branch_data}")
                else:
                    create_branch = False

            if branch_name != "":
                # Put the new file
                # Skip CI - https://docs.gitlab.com/ee/ci/pipelines/#skip-a-pipeline
                put_file_data = {
                    "branch": f"{branch_name}",
                    "content": f"{new_yml_64}",
                    "encoding": "base64",
                    "commit_message": f"[skip ci] Commit for migration regex replace replacing file '{f}'"
                }
                put_resp = self.project_repository_api.put_single_repo_file(
                    self.config.destination_host,
                    self.config.destination_token,
                    project_id,
                    f"{f}",
                    put_file_data
                )
                if not put_resp or (put_resp and put_resp.status_code == 400):
                    self.log.error(
                        f"Could not put commit for regex replace:\nproject: {project_id}\nbranch name: {branch_name}\nfile: {f}")
                # A branch_name reset would need to go here for the multiple
                # branches

    def create_staged_projects_structure(
            self, dry_run=True, disable_cicd=False):
        """Create new empty project structures for staged projects"""
        start = time()
        rotate_logs()
        staged_projects = get_staged_projects()
        host = self.config.destination_host
        token = self.config.destination_token
        for sp in tqdm(staged_projects, total=len(staged_projects), colour=self.TANUKI, desc=self.DESC, unit=self.UNIT):
            try:
                # Validate that the parent group structure exists
                path_with_namespace = sp.get("path_with_namespace")
                dst_grp_full_path = get_full_path_with_parent_namespace(
                    dirname(path_with_namespace))
                dst_grp = self.groups.find_group_by_path(
                    host, token, dst_grp_full_path)
                if dst_grp:
                    dst_gid = dst_grp.get("id")
                else:
                    self.log.error(
                        f"SKIP: Parent group {dst_grp_full_path} NOT found")
                    continue
                # Validate whether the project namespace is already reserved
                dst_path = get_dst_path_with_namespace(sp)
                dst_pid = self.find_project_by_path(host, token, dst_path)
                if dst_pid:
                    self.log.info(
                        f"SKIP: Project {dst_path} (ID: {dst_pid}) already exists")
                    continue
                name = sp.get("name")
                # Construct project metadata
                data = {
                    "name": name,
                    "path": sp.get("path"),
                    "namespace_id": dst_gid,
                    "visibility": sp.get("visibility"),
                    "description": sp.get("description"),
                    "default_branch": sp.get("default_branch")
                }
                if disable_cicd:
                    data["jobs_enabled"] = False
                    data["shared_runners_enabled"] = False
                    data["auto_devops_enabled"] = False
                self.log.info(
                    f"{get_dry_log(dry_run)}Create {dst_path} empty project structure, with payload {data}")
                if not dry_run:
                    resp = self.projects_api.create_project(
                        host, token, name, data=data)
                    if resp.status_code == 201 and sp.get(
                            "merge_requests_template"):
                        self.projects_api.edit_project(host, token, safe_json_response(resp).get(
                            "id"), {"merge_requests_template": sp["merge_requests_template"]})
                    elif resp.status_code != 201:
                        self.log.error(
                            f"Failed to create and edit project {dst_path}, with response:\n{resp} - {resp.text}")
            except RequestException as re:
                self.log.error(
                    f"Failed to create project {path_with_namespace} with error:\n{re}")
                continue
        add_post_migration_stats(start, log=self.log)

    def get_new_ids(self):
        ids = []
        staged_projects = get_staged_projects()
        if staged_projects:
            for project in staged_projects:
                try:
                    self.log.debug("Searching for existing %s" %
                                   project["name"])
                    for proj in self.projects_api.search_for_project(self.config.destination_host,
                                                                     self.config.destination_token,
                                                                     project['name']):
                        if proj["name"] == project["name"]:

                            if "%s" % project["namespace"].lower(
                            ) in proj["path_with_namespace"].lower():
                                if project["namespace"].lower(
                                ) == proj["namespace"]["name"].lower():
                                    self.log.debug("Adding {0}/{1}".format(
                                        project["namespace"], project["name"]))
                                    # self.log.info("Migrating variables for %s" % proj["name"])
                                    ids.append(proj["id"])
                                    break
                except IOError as e:
                    self.log.error(e)
            return ids

    def pull_mirror_staged_projects(self, protected_only=False, force=False, overwrite=False, dry_run=True):
        start = time()
        rotate_logs()
        staged_projects = get_staged_projects()
        src_host = self.config.source_host
        src_token = self.config.source_token
        username = self.config.mirror_username
        for sp in tqdm(staged_projects, total=len(staged_projects), colour=self.TANUKI, desc=self.DESC, unit=self.UNIT):
            mirror_pid, mirror_path = self.find_mirror_project(sp)
            sp_path = sp.get('path_with_namespace')
            sp_id = sp.get('id')
            if mirror_pid and mirror_path and username:
                self.log.info(
                    f"{get_dry_log(dry_run)}Create destination project '{mirror_path}' ({mirror_pid}) pull mirror from '{sp_path}' ({sp_id})")
                if not dry_run:
                    mirror_data = {
                        "mirror": True,
                        "mirror_trigger_builds": False,
                        "import_url": f"{strip_scheme(src_host)}://{username}:{src_token}@{strip_netloc(src_host)}/{sp_path}.git",
                        "only_mirror_protected_branches": protected_only,
                        "mirror_overwrites_diverged_branches": overwrite,
                    }
                    self.create_and_start_pull_mirror(
                        mirror_pid, mirror_path, mirror_data, force)
            else:
                self.log.error(
                    f"Failed to setup destination project '{mirror_path}' ({mirror_pid}) pull mirror from '{sp_path}' ({sp_id}) with source user '{username}'")
        add_post_migration_stats(start, log=self.log)

    def create_and_start_pull_mirror(self, mirror_pid, mirror_path, mirror_data, force):
        dst_host = self.config.destination_host
        dst_token = self.config.destination_token
        try:
            resp = self.projects_api.edit_project(
                dst_host, dst_token, mirror_pid, mirror_data)
            if resp.status_code != 200:
                self.log.error(
                    f"Failed to create project '{mirror_path}' ({mirror_pid}) pull mirror:\n{resp} - {resp.text}")
            elif force:
                self.log.info(
                    f"Start destination project '{mirror_path}' ({mirror_pid}) pull mirror")
                resp = self.projects_api.start_pull_mirror(
                    dst_host, dst_token, mirror_pid)
                if resp.status_code != 201:
                    self.log.error(
                        f"Failed to start destination project '{mirror_path}' ({mirror_pid}) pull mirror:\n{resp} - {resp.text}")
        except RequestException as re:
            self.log.error(
                f"Failed to create destination project '{mirror_path}' ({mirror_pid}) pull mirror:\n{re}")

    def delete_all_pull_mirrors(self, dry_run=True):
        ids = self.get_new_ids()
        for i in ids:
            self.mirror.remove_mirror(i, dry_run)

    def push_mirror_staged_projects(
            self, disabled=False, keep_div_refs=False, force=False, dry_run=True):
        """Create push mirror for staged projects"""
        start = time()
        rotate_logs()
        staged_projects = get_staged_projects()
        host = self.config.destination_host
        token = self.config.destination_token
        username = safe_json_response(
            self.users_api.get_current_user(host, token)).get("username")
        for sp in tqdm(staged_projects, total=len(staged_projects), colour=self.TANUKI, desc=self.DESC, unit=self.UNIT):
            try:
                dst_pid, mirror_path = self.find_mirror_project(sp)
                if dst_pid and mirror_path and username:
                    data = {
                        # username:token is GitLab.com specific.
                        # Revoking the token breaks the mirroring
                        "url": f"{strip_scheme(host)}://{username}:{token}@{strip_netloc(host)}/{mirror_path}.git",
                        "enabled": not disabled,
                        "keep_divergent_refs": keep_div_refs
                    }
                else:
                    continue
                self.log.info(
                    f"{get_dry_log(dry_run)}Create project {dst_pid} push mirror {mirror_path}")
                if not dry_run:
                    resp = self.projects_api.create_remote_push_mirror(
                        dst_pid, host, token, data=data)
                    if resp.status_code != 201:
                        self.log.error(
                            f"Failed to create project {dst_pid} push mirror to {mirror_path}, with response:\n{resp} - {resp.text}")
                    elif force:
                        # Push commit (skip-ci) to new branch and delete branch
                        self.trigger_mirroring(host, token, sp, dst_pid)
            except RequestException as re:
                self.log.error(
                    f"Failed to create project {sp.get('path_with_namespace')} push mirror, with error:\n{re}")
                continue
        add_post_migration_stats(start, log=self.log)

    def trigger_mirroring(self, host, token, staged_project, pid):
        """Force trigger a project push mirror via skip-ci commit to new branch"""
        branch = "mirroring-trigger"
        commit_data = {
            "branch": branch,
            "commit_message": f"[skip ci] {branch}",
            # retry in case of main (as of 14.0)
            "start_branch": staged_project.get("default_branch", "master"),
            "actions": [
                {
                    "action": "create",
                    "file_path": f"{branch}.txt",
                    "content": branch
                }
            ]
        }
        try:
            # Unarchive project in order to commit change and trigger mirror
            if staged_project.get("archived"):
                self.log.info(f"Unarchiving project {pid}")
                self.projects_api.unarchive_project(host, token, pid)
            commit_resp = self.project_repository_api.create_commit_with_files_and_actions(
                host, token, pid, data=commit_data)
            if commit_resp.status_code != 201:
                self.log.error(
                    f"Failed to commit branch {branch} payload {commit_data} to project {pid}, with response:\n{commit_resp}-{commit_resp.text}")
            else:
                self.projects_api.delete_branch(
                    host, token, pid, branch)
        except RequestException as re:
            self.log.error(
                f"Failed to commit branch {branch} payload {commit_data} to project {pid}, with error:\n{re}")
        finally:
            if staged_project.get("archived"):
                self.log.info(f"Archiving back project {pid}")
                self.projects_api.archive_project(host, token, pid)

    def toggle_staged_projects_push_mirror(self, disable=False, dry_run=True):
        """Enable/disable project push mirror for staged projects"""
        start = time()
        rotate_logs()
        staged_projects = get_staged_projects()
        host = self.config.destination_host
        token = self.config.destination_token
        for sp in tqdm(staged_projects, total=len(staged_projects), colour=self.TANUKI, desc=self.DESC, unit=self.UNIT):
            try:
                dst_pid, mirror_path = self.find_mirror_project(sp)
                project = f"project {sp.get('path_with_namespace')} (ID: {dst_pid})"
                if dst_pid and mirror_path:
                    # Match mirror based on URL and get ID
                    url = f"{strip_netloc(host)}/{mirror_path}.git"
                    mirror_id = None
                    for m in self.projects_api.get_all_remote_push_mirrors(
                            dst_pid, host, token):
                        is_error, resp = is_error_message_present(m)
                        if is_error or not resp:
                            self.log.error(
                                f"Invalid {project} push mirror:\n{json_pretty(resp)}")
                        elif url in m.get("url", ""):
                            mirror_id = m.get("id")
                            data = {
                                "mirror_id": mirror_id,
                                "enabled": not disable
                            }
                    if not mirror_id:
                        self.log.error(
                            f"SKIP: {project} push mirror to {url} NOT found")
                        continue
                else:
                    continue
                self.log.info(
                    f"{get_dry_log(dry_run)}Toggle {project} push mirror {mirror_path}, with payload {data}")
                if not dry_run:
                    resp = self.projects_api.edit_remote_push_mirror(
                        dst_pid, mirror_id, host, token, data=data)
                    if resp.status_code != 200:
                        self.log.error(
                            f"Failed to {'disable' if disable else 'enable'} {project} push mirror to {mirror_path}, with response:\n{resp} - {resp.text}")
            except RequestException as re:
                self.log.error(
                    f"Failed to toggle project {sp.get('path_with_namespace')} push mirror, with error:\n{re}")
                continue
        add_post_migration_stats(start, log=self.log)

    def verify_staged_projects_push_mirror(self, disabled=False, keep_div_refs=False):
        """Verify that the project push mirror exists and is not failing"""
        start = time()
        rotate_logs()
        staged_projects = get_staged_projects()
        host = self.config.destination_host
        token = self.config.destination_token
        for sp in tqdm(staged_projects, total=len(staged_projects), colour=self.TANUKI, desc=self.DESC, unit=self.UNIT):
            try:
                self.verify_staged_projects(
                    host, token, sp, disabled, keep_div_refs)
            except RequestException as re:
                self.log.error(
                    f"Failed to verify project {sp.get('path_with_namespace')} push mirror, with error:\n{re}")
                continue
        add_post_migration_stats(start, log=self.log)

    def verify_staged_projects(self, host, token, sp, disabled, keep_div_refs):
        dst_pid, mirror_path = self.find_mirror_project(sp)
        project = f"'{sp.get('path_with_namespace')}' (ID: {dst_pid})"
        if dst_pid and mirror_path:
            url = f"{strip_netloc(host)}/{mirror_path}.git"
            self.verify_push_mirror(self.projects_api.get_all_remote_push_mirrors(
                dst_pid, host, token), project, url, disabled, keep_div_refs)

    def verify_push_mirror(self, mirrors, project, url, disabled, keep_div_refs):
        """Loop over project push mirrors, match based on URL and verify its state"""
        missing = True
        for m in mirrors:
            is_error, resp = is_error_message_present(m)
            if is_error or not resp:
                self.log.error(
                    f"Invalid project {project} push mirror:\n{json_pretty(resp)}")
                break
            if url in m.get("url", ""):
                missing = False
                if m.get("update_status") == "failed":
                    self.log.error(
                        f"Failed project {project} push mirror, with status:\n{json_pretty(m)}")
                if m.get("keep_divergent_refs") != (keep_div_refs):
                    self.log.error(
                        f"Project {project} push mirror 'keep_divergent_refs' set to: {m.get('keep_divergent_refs')}")
                if m.get("enabled") != (not disabled):
                    self.log.error(
                        f"Project {project} push mirror 'enabled' set to: {m.get('enabled')}")
                break
        if missing:
            self.log.error(f"Missing project {project} push mirror {url}")

    def find_mirror_project(self, staged_project):
        """Validate pull/push mirror source and destination project"""
        try:
            orig_path = get_dst_path_with_namespace(
                staged_project, mirror=True)
            orig_pid = self.find_project_by_path(
                self.config.source_host, self.config.source_token, orig_path)
            if not orig_pid:
                self.log.error(
                    f"SKIP: Original project '{orig_path}' NOT found")
                return (False, False)
            mirror_path = get_dst_path_with_namespace(staged_project)
            mirror_pid = self.find_project_by_path(
                self.config.destination_host, self.config.destination_token, mirror_path)
            if not mirror_pid:
                self.log.error(
                    f"SKIP: Mirror project '{mirror_path}' NOT found")
                return (mirror_pid, False)
            return (mirror_pid, mirror_path)
        except RequestException as re:
            self.log.error(
                f"Failed to find staged project '{staged_project.get('path_with_namespace')}' original and/or mirror project:\n{re}")
            return (False, False)

    def delete_staged_projects_push_mirrors(self, remove_all=False, dry_run=True):
        start = time()
        rotate_logs()
        staged_projects = get_staged_projects()
        host = self.config.destination_host
        token = self.config.destination_token
        for sp in tqdm(staged_projects, total=len(staged_projects), colour=self.TANUKI, desc=self.DESC, unit=self.UNIT):
            sp_path = sp.get("path_with_namespace")
            try:
                orig_pid = self.find_project_by_path(host, token, sp_path)
                if not orig_pid:
                    self.log.warning(
                        f"SKIP: Original project {sp_path} NOT found")
                    continue
                self.delete_push_mirrors(
                    host, token, orig_pid, sp_path, remove_all, dry_run)
            except RequestException as re:
                self.log.error(
                    f"Failed to DELETE project '{sp_path}' push mirror, with error:\n{re}")
                continue
        add_post_migration_stats(start, log=self.log)

    def delete_push_mirrors(self, host, token, orig_pid, sp_path, remove_all, dry_run):
        # Look for mirrors to destination host / destination parent group path (if configured)
        url = f"{strip_netloc(host)}{('/' + self.config.dstn_parent_group_path) if self.config.dstn_parent_group_path else ''}"
        missing = True
        for mirror in self.projects_api.get_all_remote_push_mirrors(orig_pid, host, token):
            is_error, resp = is_error_message_present(mirror)
            if is_error or not resp:
                self.log.error(
                    f"Invalid project '{sp_path}' push mirror:\n{json_pretty(resp)}")
                break
            url_present = url in mirror.get("url", "")
            if not dry_run and (remove_all or url_present):
                missing = False
                resp = self.projects_api.delete_remote_push_mirror(
                    host, token, orig_pid, mirror.get("id"))
                if resp.status_code != 204:
                    self.log.error(
                        f"Failed to delete project '{sp_path}' push mirror '{url if url_present else mirror.get('url','')}', with response:\n{resp} - {resp.text}")
        if not dry_run and missing:
            self.log.error(
                f"Missing project '{sp_path}' push mirror {url}")

    def create_staged_projects_fork_relation(self, dry_run=True):
        start = time()
        rotate_logs()
        staged_projects = get_staged_projects()
        host = self.config.destination_host
        token = self.config.destination_token
        for sp in tqdm(staged_projects, total=len(staged_projects), colour=self.TANUKI, desc=self.DESC, unit=self.UNIT):
            orig_project = sp.get("forked_from_project")
            # Cannot validate destination user namespace without email
            if orig_project and not is_user_project(orig_project):
                try:
                    # Validate fork source and destination project
                    fork_path = get_dst_path_with_namespace(sp)
                    fork_pid = self.find_project_by_path(
                        host, token, fork_path)
                    if not fork_pid:
                        self.log.error(
                            f"SKIP: Fork project {fork_path} NOT found")
                        continue
                    orig_path = get_dst_path_with_namespace(orig_project)
                    orig_pid = self.find_project_by_path(
                        host, token, orig_path)
                    if not orig_pid:
                        self.log.error(
                            f"SKIP: Fork {fork_path} forked from project {orig_path} NOT found")
                        continue
                    self.log.info(
                        f"{get_dry_log(dry_run)}Create forked from {orig_path} to {fork_path} project relation")
                    if not dry_run:
                        resp = self.projects_api.create_project_fork_relation(
                            fork_pid, orig_pid, host, token)
                        if resp.status_code != 201:
                            self.log.error(
                                f"Failed to create forked from {orig_path} to {fork_path} project relation, with response {resp} - {resp.text}")
                except RequestException as re:
                    self.log.error(
                        f"Failed to create project {sp.get('path_with_namespace')} fork relation, with error:\n{re}")
                    continue
        add_post_migration_stats(start, log=self.log)

    def perform_url_rewrite_only(self, dry_run=True):
        """
            :param dry_run: (bool) Should this be a dry_run. Default=True

            Entry point for the stand-alone URL rewrite functionality (instead of running as a post-migration step on project import)
            Does some preliminary data checks, then spawns the multiprocessing call of handle_rewriting_project_yaml
        """
        self.dry_run = dry_run
        if not self.config.remapping_file_path:
            self.log.error(
                f"{get_dry_log(dry_run)}Remapping file path not set. Set remapping_file_path under [APP] in the congregate.conf")
            return
        staged_projects = get_staged_projects()

        if staged_projects:
            if check_for_staged_user_projects(staged_projects):
                return
            rewrite_results = list(rr for rr in self.multi.start_multi_process(
                self.handle_rewriting_project_yaml, staged_projects, processes=self.config.processes))

            self.log.info(
                f"### {get_dry_log(dry_run)}Project URL rewrite results ###\n{json_pretty(rewrite_results)}")

    def handle_rewriting_project_yaml(self, project):
        """
            :param project: (dict) The project for which we are performing the rewrite. Is a staged_project entry
            :param dry_run: (bool) Should this be a dry_run. Default=True

            This function will not work if the project does not exist on the destination.
            Attempts to locate the staged project on the destination, and if found, performs the url rewrite
            Will generally be called by perform_url_rewrite_only, but can be called individually for one-off
            Using DRY-RUN is a good way to check the data on the destination system. It will search, log, etc
            but will not attempt to do the rewrite. A good way to make sure all expected projects are created.
        """
        return_dict = None
        try:
            import_id = None
            dst_path_with_namespace = None
            dst_path_with_namespace = get_dst_path_with_namespace(project)
            self.log.info(f"{dst_path_with_namespace}")
            dst_pid = self.find_project_by_path(
                self.config.destination_host, self.config.destination_token, dst_path_with_namespace)
            if dst_pid:
                # As this is a stand-alone run, we will make an assumption that the project is imported, and skip the import check
                self.log.info(
                    f"{get_dry_log(self.dry_run)}Project {dst_path_with_namespace} (ID: {dst_pid}) found on destination.")
                import_id = dst_pid
            else:
                self.log.error(
                    f"{get_dry_log(self.dry_run)}Project {dst_path_with_namespace} NOT found on destination. URL rewrite will not be performed.")
                raise DataError(f"Project {dst_path_with_namespace} not found")

            # Always log
            self.log.info(
                f"{get_dry_log(self.dry_run)}Performing rewrite for project {dst_path_with_namespace} with ID {import_id}")

            # Perform the replacement using the existing code
            if import_id and not self.dry_run:
                self.migrate_gitlab_variable_replace_ci_yml(import_id)
        except Exception as ex:
            return_dict = {"id": import_id, "path": dst_path_with_namespace,
                           "message": "error", "exception": str(ex)}
        finally:
            return return_dict or {"id": import_id, "path": dst_path_with_namespace, "message": "success", "exception": None}

    def list_staged_projects_contributors(self, dry_run=True):
        start = time()
        rotate_logs()
        contributors = []
        staged_projects = get_staged_projects()
        open(f"{self.app_path}/data/staged_users.json", "w").close()
        for c in self.multi.start_multi_process(
                self.list_project_contributors,
                staged_projects,
                processes=self.config.processes):
            contributors.extend(c)
        contributors = remove_dupes(contributors)
        self.log.info(
            f"{get_dry_log(dry_run)}Saving {len(contributors)} unique contributors to file")
        if not dry_run:
            with open(f"{self.app_path}/data/staged_users.json", "w") as f:
                json.dump(contributors, f, indent=4)
        add_post_migration_stats(start, log=self.log)

    def list_project_contributors(self, staged_project):
        contributors = []
        project_id = staged_project.get("id")
        project_path = staged_project.get('path_with_namespace')
        try:
            c_retention = None
            c_retention = ContributorRetentionClient(
                project_id, None, project_path)
            if contributor_map := c_retention.build_map():
                for contributor, data in contributor_map.items():
                    self.log.info(
                        f"Retrieved contributor '{contributor}' from project '{project_path}'")
                    contributors.append(data)
            else:
                self.log.info(
                    f"No contributors found for project '{project_path}'")
        except RequestException as re:
            self.log.error(
                f"Failed to list project '{project_path}' contributors, with error:\n{re}")
        return contributors


@shared_task(name='retrieve-projects')
@mongo_connection
def handle_retrieving_project(host, token, project, mongo=None):
    pc = ProjectsClient()
    error, project = is_error_message_present(project)
    if error or not project:
        pc.log.error(f"Failed to list project:\n{project}")
    else:
        for k in constants.PROJECT_KEYS_TO_IGNORE:
            project.pop(k, None)
        project["members"] = [] if pc.skip_project_members else list(
            pc.projects_api.get_members(project["id"], host, token))
        mongo.insert_data(f"projects-{strip_netloc(host)}", project)
