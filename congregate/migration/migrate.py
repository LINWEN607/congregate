"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2020 - GitLab
"""

import os
import json
from time import sleep, time
from traceback import print_exc
from requests.exceptions import RequestException

from congregate.helpers import api
from congregate.helpers.migrate_utils import get_export_filename_from_namespace_and_name, get_dst_path_with_namespace, get_full_path_with_parent_namespace, \
    is_top_level_group, get_failed_export_from_results, get_results, get_staged_groups_without_failed_export, get_staged_projects_without_failed_export, can_migrate_users
from congregate.helpers.misc_utils import get_dry_log, json_pretty, is_dot_com, clean_data, add_post_migration_stats, \
    rotate_logs, write_results_to_file, migration_dry_run, safe_json_response, is_error_message_present, get_duplicate_paths
from congregate.helpers.jobtemplategenerator import JobTemplateGenerator
from congregate.helpers.processes import start_multi_process
from congregate.cli.stage_projects import ProjectStageCLI
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.importexport import ImportExportClient
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.migration.gitlab.api.namespaces import NamespacesApi
from congregate.migration.gitlab.pushrules import PushRulesClient
from congregate.migration.gitlab.merge_request_approvals import MergeRequestApprovalsClient
from congregate.migration.gitlab.registries import RegistryClient
from congregate.migration.mirror import MirrorClient
from congregate.migration.gitlab.keys import KeysClient
from congregate.migration.gitlab.hooks import HooksClient
from congregate.migration.gitlab.environments import EnvironmentsClient
from congregate.migration.gitlab.external_import import ImportClient
from congregate.migration.jenkins.base import JenkinsClient
from congregate.migration.teamcity.base import TeamcityClient


class MigrateClient(BaseClass):
    BLOCKED = ["blocked", "ldap_blocked", "deactivated"]

    def __init__(
        self,
        dry_run=True,
        processes=None,
        only_post_migration_info=False,
        start=time(),
        skip_users=False,
        hard_delete=False,
        skip_groups=False,
        skip_projects=False,
        skip_group_export=False,
        skip_group_import=False,
        skip_project_export=False,
        skip_project_import=False
    ):
        self.ie = ImportExportClient()
        self.mirror = MirrorClient()
        self.variables = VariablesClient()
        self.users = UsersClient()
        self.users_api = UsersApi()
        self.groups = GroupsClient()
        self.groups_api = GroupsApi()
        self.projects = ProjectsClient()
        self.projects_api = ProjectsApi()
        self.project_repository_api = ProjectRepositoryApi()
        self.namespaces_api = NamespacesApi()
        self.pushrules = PushRulesClient()
        self.mr_approvals = MergeRequestApprovalsClient()
        self.registries = RegistryClient()
        self.keys = KeysClient()
        self.hooks = HooksClient()
        self.environments = EnvironmentsClient()
        self.ext_import = ImportClient()
        super(MigrateClient, self).__init__()
        self.jenkins = JenkinsClient() if self.config.ci_source_type == "jenkins" else None
        self.teamcity = TeamcityClient() if self.config.ci_source_type == "teamcity" else None
        self.job_template = JobTemplateGenerator()

        self.dry_run = dry_run
        self.processes = processes
        self.only_post_migration_info = only_post_migration_info
        self.start = start
        self.skip_users = skip_users
        self.hard_delete = hard_delete
        self.skip_groups = skip_groups
        self.skip_projects = skip_projects
        self.skip_group_export = skip_group_export
        self.skip_group_import = skip_group_import
        self.skip_project_export = skip_project_export
        self.skip_project_import = skip_project_import

    def migrate(self):
        self.log.info(
            f"{get_dry_log(self.dry_run)}Migrating data from {self.config.source_host} ({self.config.source_type}) to {self.config.destination_host}")

        # Dry-run and log cleanup
        if self.dry_run:
            clean_data(dry_run=False, files=[
                "dry_run_user_migration.json",
                "dry_run_group_migration.json",
                "dry_run_project_migration.json"])
        rotate_logs()
        if self.config.source_type == "gitlab":
            self.migrate_from_gitlab()
        elif self.config.source_type == "bitbucket server":
            self.migrate_from_bitbucket_server()
        elif self.config.source_type == "github":
            self.migrate_from_github()
        else:
            self.log.warning(
                f"Configuration (data/congregate.conf) src_type {self.config.source_type} not supported")
        add_post_migration_stats(self.start, log=self.log)

    def migrate_from_gitlab(self):
        # Migrate users
        self.migrate_user_info()

        # Migrate groups
        self.migrate_group_info()

        # Migrate projects
        self.migrate_project_info()

        # Migrate system hooks
        self.hooks.migrate_system_hooks(dry_run=self.dry_run)

        # Remove import user from parent group to avoid inheritance (self-managed only)
        if not self.dry_run and self.config.dstn_parent_id and not is_dot_com(self.config.destination_host):
            self.groups.remove_import_user(self.config.dstn_parent_id)

    def migrate_from_github(self):
        dry_log = get_dry_log(self.dry_run)

        # Migrate users
        self.migrate_user_info()

        # Migrate GH orgs/teams to groups/sub-groups
        staged_groups = self.groups.get_staged_groups()
        if staged_groups and not self.skip_group_import:
            self.log.info(
                f"{dry_log}Migrating GitHub orgs/teams to GitLab groups/sub-groups")
            results = start_multi_process(
                self.migrate_github_group, staged_groups, processes=self.processes)

            self.are_results(results, "group", "import")

            results.append(get_results(results))
            self.log.info(
                f"### {dry_log}Group import results ###\n{json_pretty(results)}")
            write_results_to_file(
                results, result_type="group", log=self.log)
        else:
            self.log.info("SKIP: No projects to migrate")

        # Migrate GH repos to projects
        staged_projects = self.projects.get_staged_projects()
        if staged_projects and not self.skip_project_import:
            self.log.info("Importing projects from GitHub")
            import_results = start_multi_process(
                self.import_github_project, staged_projects, processes=self.processes)

            self.are_results(import_results, "project", "import")

            # append Total : Successful count of project imports
            import_results.append(get_results(import_results))
            self.log.info(
                f"### {dry_log}Project import results ###\n{json_pretty(import_results)}")
            write_results_to_file(import_results, log=self.log)
        else:
            self.log.info("SKIP: No projects to migrate")

    def migrate_github_group(self, group):
        result = False
        members = group.pop("members")
        group["full_path"] = get_full_path_with_parent_namespace(
            group["full_path"])
        if not self.dry_run:
            # Wait for parent group to create
            if self.config.dstn_parent_group_path is not None:
                pnamespace = self.groups.wait_for_parent_group_creation(group)
                if not pnamespace:
                    return {
                        group["full_path"]: False
                    }
            group["parent_id"] = safe_json_response(
                pnamespace)["id"] if group["parent_id"] else self.config.dstn_parent_id
            if group.get("description", None) is None:
                group["description"] = ""
            result = safe_json_response(self.groups_api.create_group(
                self.config.destination_host, self.config.destination_token, group))
            if result and not is_error_message_present(result):
                group_id = result.get("id", None)
                if group_id:
                    result["members"] = self.groups.add_members_to_destination_group(
                        self.config.destination_host, self.config.destination_token, group_id, members)
                    self.groups.remove_import_user(group_id)
        return {
            group["full_path"]: result
        }

    def import_github_project(self, project):
        members = project.pop("members")
        result = self.ext_import.trigger_import_from_ghe(
            project, dry_run=self.dry_run)
        sleep(10)
        if result.get(project["path_with_namespace"], False) is not False:
            project_id = result[project["path_with_namespace"]
                                ]["response"].get("id")
            result[project["path_with_namespace"]]["members"] = self.projects.add_members_to_destination_project(
                self.config.destination_host, self.config.destination_token, project_id, members)
            if self.config.ci_source_type == "jenkins":
                result[project["path_with_namespace"]]["jenkins_variables"] = self.migrate_jenkins_variables(
                    project, project_id)
            if self.config.ci_source_type == "teamcity":
                result[project["path_with_namespace"]]["teamcity_variables"] = self.migrate_teamcity_variables(
                    project, project_id)
            self.projects.remove_import_user(project_id)
            # Added a new file in the repo
            result[project["path_with_namespace"]]["is_gh_pages"] = self.add_pipeline_for_github_pages(
                project_id)
        return result

    def add_pipeline_for_github_pages(self, project_id):
        '''
        GH pages utilizes a separate branch (gh-pages) for its pages feature.
        We lookup the branch on destination once the project imports and add the .gitlab-ci.yml file
        '''

        is_result = False
        data = {
            "branch": "gh-pages",
            "commit_message": "Adding .gitlab-ci.yml for publishing GitHub pages",
            "content": self.job_template.generate_plain_html_template()
        }
        branches = list(self.project_repository_api.get_all_project_repository_branches(project_id,
                                                                                        self.config.destination_host, self.config.destination_token))
        for branch in branches:
            if branch["name"] == "gh-pages":
                is_result = True
                project = self.project_repository_api.create_repo_file(
                    self.config.destination_host, self.config.destination_token,
                    project_id, ".gitlab-ci.yml", data)
        return is_result

    def migrate_from_bitbucket_server(self):
        dry_log = get_dry_log(self.dry_run)

        # Migrate users
        self.migrate_user_info()

        # Migrate BB projects to groups
        staged_groups = self.groups.get_staged_groups()
        if staged_groups and not self.skip_group_import:
            self.log.info(
                f"{dry_log}Migrating BitBucket projects to GitLab groups")
            results = start_multi_process(
                self.migrate_bitbucket_group, staged_groups, processes=self.processes)

            self.are_results(results, "group", "import")

            results.append(get_results(results))
            self.log.info("### {0}Group import results ###\n{1}"
                          .format(dry_log, json_pretty(results)))
            write_results_to_file(
                results, result_type="group", log=self.log)
        else:
            self.log.info("SKIP: No projects to migrate")

        # Migrate BB repos to projects
        staged_projects = self.projects.get_staged_projects()
        if staged_projects and not self.skip_project_import:
            self.log.info("Importing projects from BitBucket Server")
            import_results = start_multi_process(
                self.import_bitbucket_project, staged_projects, processes=self.processes)

            self.are_results(import_results, "project", "import")

            # append Total : Successful count of project imports
            import_results.append(get_results(import_results))
            self.log.info("### {0}Project import results ###\n{1}"
                          .format(dry_log, json_pretty(import_results)))
            write_results_to_file(import_results, log=self.log)
        else:
            self.log.info("SKIP: No projects to migrate")

    def migrate_bitbucket_group(self, group):
        result = False
        members = group.pop("members")
        group["full_path"] = get_full_path_with_parent_namespace(
            group["full_path"])
        group["parent_id"] = self.config.dstn_parent_id
        if not self.dry_run:
            result = safe_json_response(self.groups_api.create_group(
                self.config.destination_host, self.config.destination_token, group))
            if result and not is_error_message_present(result):
                group_id = result.get("id", None)
                if group_id:
                    result["members"] = self.groups.add_members_to_destination_group(
                        self.config.destination_host, self.config.destination_token, group_id, members)
                    self.groups.remove_import_user(group_id)
        return {
            group["full_path"]: result
        }

    def import_bitbucket_project(self, project):
        members = project.pop("members")
        result = self.ext_import.trigger_import_from_bb_server(
            project, dry_run=self.dry_run)
        if result.get(project["path_with_namespace"], False) is not False:
            project_id = result[project["path_with_namespace"]
                                ]["response"].get("id")
            result["members"] = self.projects.add_members_to_destination_project(
                self.config.destination_host, self.config.destination_token, project_id, members)
            self.projects.remove_import_user(project_id)
        return result

    def are_results(self, results, var, stage):
        if not results:
            self.log.warning(
                "Results from {0} {1} returned as empty. Aborting.".format(var, stage))
            add_post_migration_stats(self.dry_run, log=self.log)
            exit()

    def migrate_user_info(self):
        staged_users = self.users.get_staged_users()
        if staged_users and can_migrate_users(staged_users):
            if not self.skip_users:
                self.log.info("{}Migrating user info".format(
                    get_dry_log(self.dry_run)))
                staged = self.users.handle_users_not_found(
                    "staged_users", self.users.search_for_staged_users()[0], keep=False if self.only_post_migration_info else True)
                new_users = start_multi_process(
                    self.handle_user_creation, staged, self.processes)
                self.are_results(new_users, "user", "creation")
                formatted_users = {}
                for nu in new_users:
                    formatted_users[nu["email"]] = nu
                new_users.append(get_results(new_users))
                self.log.info("### {0}User creation results ###\n{1}"
                              .format(get_dry_log(self.dry_run), json_pretty(new_users)))
                write_results_to_file(
                    formatted_users, result_type="user", log=self.log)
                if self.dry_run:
                    self.log.info(
                        "DRY-RUN: Outputing various USER migration data to dry_run_user_migration.json")
                    migration_dry_run("user", list(start_multi_process(
                        self.users.generate_user_data, staged_users, self.processes)))
            else:
                self.log.info(
                    "SKIP: Assuming staged users are already migrated")
        else:
            self.log.info("SKIP: No users to migrate")

    def handle_user_creation(self, user):
        """
            This is called when importing staged_users.json.
            Blocked users will be skipped if we do NOT 'keep_blocked_users'.

            :param user: Each iterable called is a user from the staged_users.json file
            :return:
        """
        response = None
        state = user.get("state", None).lower()
        email = user.get("email", None)
        new_user = {
            "email": email,
            "id": None
        }
        old_user = {
            "email": email,
            "id": user.get("id", None)
        }
        try:
            if not self.only_post_migration_info:
                if state == "active" or (state in self.BLOCKED and self.config.keep_blocked_users):
                    user_data = self.users.generate_user_data(user)
                    self.log.info("{0}Attempting to create user {1}".format(
                        get_dry_log(self.dry_run), email))
                    response = self.users_api.create_user(
                        self.config.destination_host, self.config.destination_token, user_data) if not self.dry_run else None
                else:
                    self.log.info("SKIP: Not migrating {0} user:\n{1}".format(
                        state, json_pretty(user)))
                if response is not None:
                    # NOTE: Persist 'blocked' user state regardless of domain and creation status.
                    if user_data.get("state", None).lower() in self.BLOCKED:
                        self.users.block_user(user_data)
                    new_user = self.users.handle_user_creation_status(
                        response, user_data)
            if not self.dry_run and self.config.source_type == "gitlab":
                found_user = new_user if new_user.get(
                    "id", None) is not None else self.users.find_user_by_email_comparison_without_id(email)
                new_user["id"] = found_user.get(
                    "id", None) if found_user else None
                if found_user:
                    # Migrate SSH keys
                    self.keys.migrate_user_ssh_keys(old_user, new_user)
                    # Migrate GPG keys
                    self.keys.migrate_user_gpg_keys(old_user, new_user)
        except RequestException as e:
            self.log.error(
                "Failed to create user {0}, with error:\n{1}".format(user_data, e))
        except Exception as e:
            self.log.error(
                "Could not get response text/JSON. Error was {0}".format(e))
            self.log.error(print_exc(e))
        return new_user

    def migrate_group_info(self):
        staged_groups = self.groups.get_staged_groups()
        self.log.info("Duplicate group paths:\n{}".format(
            get_duplicate_paths(staged_groups, are_projects=False)))
        staged_top_groups = [g for g in staged_groups if is_top_level_group(g)]
        dry_log = get_dry_log(self.dry_run)
        if staged_groups:
            if not self.skip_group_export:
                self.log.info("{}Exporting groups".format(dry_log))
                export_results = start_multi_process(
                    self.handle_exporting_groups, staged_top_groups, processes=self.processes)

                self.are_results(export_results, "group", "export")

                # Create list of groups that failed export
                failed = get_failed_export_from_results(
                    export_results)
                self.log.warning("SKIP: Groups that failed to export or already exist on destination:\n{}".format(
                    json_pretty(failed)))

                # Append total count of groups exported
                export_results.append(get_results(export_results))
                self.log.info("### {0}Group export results ###\n{1}"
                              .format(dry_log, json_pretty(export_results)))

                # Filter out the failed ones
                staged_top_groups = get_staged_groups_without_failed_export(
                    staged_top_groups, failed)
            else:
                self.log.info(
                    "SKIP: Assuming staged groups are already exported")
            if not self.skip_group_import:
                self.log.info("{}Importing groups".format(dry_log))
                import_results = start_multi_process(
                    self.handle_importing_groups, staged_top_groups, processes=self.processes)

                self.are_results(import_results, "group", "import")

                # append Total : Successful count of groups imports
                import_results.append(get_results(import_results))
                self.log.info("### {0}Group import results ###\n{1}"
                              .format(dry_log, json_pretty(import_results)))
                write_results_to_file(
                    import_results, result_type="group", log=self.log)

                # Migrate sub-group info
                staged_subgroups = [
                    g for g in staged_groups if not is_top_level_group(g)]
                if staged_subgroups:
                    start_multi_process(self.migrate_subgroup_info,
                                        staged_subgroups, processes=self.processes)
            else:
                self.log.info(
                    "SKIP: Assuming staged groups will be later imported")
        else:
            self.log.info("SKIP: No groups to migrate")

    def handle_exporting_groups(self, group):
        full_path = group["full_path"]
        gid = group["id"]
        dry_log = get_dry_log(self.dry_run)
        filename = get_export_filename_from_namespace_and_name(
            full_path)
        result = {
            filename: False
        }
        try:
            self.log.info("{0}Exporting group {1} (ID: {2}) as {3}"
                          .format(dry_log, full_path, gid, filename))
            result[filename] = self.ie.export_group(
                gid, full_path, filename, dry_run=self.dry_run)
        except (IOError, RequestException) as oe:
            self.log.error("Failed to export group {0} (ID: {1}) as {2} with error:\n{3}".format(
                full_path, gid, filename, oe))
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())
        return result

    def handle_importing_groups(self, group):
        full_path = group["full_path"]
        src_gid = group["id"]
        full_path_with_parent_namespace = get_full_path_with_parent_namespace(
            full_path)
        filename = get_export_filename_from_namespace_and_name(
            full_path)
        result = {
            full_path_with_parent_namespace: False
        }
        import_id = None
        try:
            if isinstance(group, str):
                group = json.loads(group)
            self.log.info("Searching on destination for group {}".format(
                full_path_with_parent_namespace))
            dst_grp = self.groups.find_group_by_path(
                self.config.destination_host, self.config.destination_token, full_path_with_parent_namespace)
            dst_gid = dst_grp.get("id", None) if dst_grp else None
            if dst_gid:
                self.log.info("{0}Group {1} (ID: {2}) already exists on destination".format(
                    get_dry_log(self.dry_run), full_path, dst_gid))
                result[full_path_with_parent_namespace] = dst_gid
                if self.only_post_migration_info and not self.dry_run:
                    import_id = dst_gid
                    group = dst_grp
                else:
                    result[full_path_with_parent_namespace] = dst_gid
            else:
                self.log.info("{0}Group {1} NOT found on destination, importing..."
                              .format(get_dry_log(self.dry_run), full_path_with_parent_namespace))
                self.ie.import_group(
                    group, full_path_with_parent_namespace, filename, dry_run=self.dry_run)
                # In place of checking the import status
                if not self.dry_run:
                    group = self.ie.wait_for_group_import(
                        full_path_with_parent_namespace)
                    import_id = group.get("id", None)
            if import_id and not self.dry_run:
                result[full_path_with_parent_namespace] = group
                self.migrate_single_group_features(
                    src_gid, import_id, full_path)
        except (RequestException, KeyError, OverflowError) as oe:
            self.log.error("Failed to import group {0} (ID: {1}) as {2} with error:\n{3}".format(
                full_path, src_gid, filename, oe))
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())
        return result

    def migrate_subgroup_info(self, subgroup):
        full_path = subgroup["full_path"]
        src_gid = subgroup["id"]
        full_path_with_parent_namespace = get_full_path_with_parent_namespace(
            full_path)
        try:
            if isinstance(subgroup, str):
                subgroup = json.loads(subgroup)
            self.log.info("Searching on destination for sub-group {}".format(
                full_path_with_parent_namespace))
            dst_gid = self.groups.find_group_id_by_path(
                self.config.destination_host, self.config.destination_token, full_path_with_parent_namespace)
            if dst_gid:
                self.log.info("{0}Sub-group {1} (ID: {2}) found on destination".format(
                    get_dry_log(self.dry_run), full_path, dst_gid))
                if not self.dry_run:
                    self.migrate_single_group_features(
                        src_gid, dst_gid, full_path)
            else:
                self.log.info("{0}Sub-group {1} NOT found on destination".format(
                    get_dry_log(self.dry_run), full_path_with_parent_namespace))
        except (RequestException, KeyError, OverflowError) as oe:
            self.log.error(
                "Failed to migrate sub-group {0} (ID: {1}) info with error:\n{2}".format(full_path, src_gid, oe))
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())

    def migrate_single_group_features(self, src_gid, dst_gid, full_path):
        # CI/CD Variables
        self.variables.migrate_gitlab_cicd_variables(
            src_gid, dst_gid, full_path, "group")

        # Hooks (Webhooks)
        self.hooks.migrate_group_hooks(src_gid, dst_gid, full_path)

        # Remove import user
        self.groups.remove_import_user(dst_gid)

    def migrate_project_info(self):
        staged_projects = self.projects.get_staged_projects()
        self.log.info("Duplicate project paths:\n{}".format(
            get_duplicate_paths(staged_projects)))
        dry_log = get_dry_log(self.dry_run)
        if staged_projects:
            if not self.skip_project_export:
                self.log.info("{}Exporting projects".format(dry_log))
                export_results = start_multi_process(
                    self.handle_exporting_projects, staged_projects, processes=self.processes)

                self.are_results(export_results, "project", "export")
                # Create list of projects that failed export
                failed = get_failed_export_from_results(
                    export_results)
                self.log.warning("SKIP: Projects that failed to export or already exist on destination:\n{}".format(
                    json_pretty(failed)))

                # Append total count of projects exported
                export_results.append(get_results(export_results))
                self.log.info("### {0}Project export results ###\n{1}"
                              .format(dry_log, json_pretty(export_results)))

                # Filter out the failed ones
                staged_projects = get_staged_projects_without_failed_export(
                    staged_projects, failed)
            else:
                self.log.info(
                    "SKIP: Assuming staged projects are already exported")

            if not self.skip_project_import:
                self.log.info("{}Importing projects".format(dry_log))
                import_results = start_multi_process(
                    self.handle_importing_projects, staged_projects, processes=self.processes)

                self.are_results(import_results, "project", "import")

                # append Total : Successful count of project imports
                import_results.append(get_results(import_results))
                self.log.info("### {0}Project import results ###\n{1}"
                              .format(dry_log, json_pretty(import_results)))
                write_results_to_file(import_results, log=self.log)
            else:
                self.log.info(
                    "SKIP: Assuming staged projects will be later imported")
        else:
            self.log.info("SKIP: No projects to migrate")

    def handle_exporting_projects(self, project):
        name = project["name"]
        namespace = project["namespace"]
        pid = project["id"]
        dry_log = get_dry_log(self.dry_run)
        filename = get_export_filename_from_namespace_and_name(
            namespace, name)
        result = {
            filename: False
        }
        try:
            self.log.info("{0}Exporting project {1} (ID: {2}) as {3}"
                          .format(dry_log, project["path_with_namespace"], pid, filename))
            result[filename] = self.ie.export_project(
                project, dry_run=self.dry_run)
        except (IOError, RequestException) as oe:
            self.log.error("Failed to export project {0} (ID: {1}) as {2} with error:\n{3}".format(
                name, pid, filename, oe))
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())
        return result

    def handle_importing_projects(self, project_json):
        src_id = project_json["id"]
        archived = project_json["archived"]
        path = project_json["path_with_namespace"]
        dst_path_with_namespace = get_dst_path_with_namespace(
            project_json)
        result = {
            dst_path_with_namespace: False
        }
        import_id = None
        try:
            if isinstance(project_json, str):
                project_json = json.loads(project_json)
            dst_pid = self.projects.find_project_by_path(
                self.config.destination_host, self.config.destination_token, dst_path_with_namespace)
            if dst_pid:
                import_status = self.projects_api.get_project_import_status(
                    self.config.destination_host, self.config.destination_token, dst_pid).json()
                self.log.info("Project {0} (ID: {1}) found on destination, with import status: {2}".format(
                    dst_path_with_namespace, dst_pid, import_status))
                if self.only_post_migration_info and not self.dry_run:
                    import_id = dst_pid
                else:
                    result[dst_path_with_namespace] = dst_pid
            else:
                self.log.info("{0}Project {1} NOT found on destination, importing...".format(
                    get_dry_log(self.dry_run), dst_path_with_namespace))
                import_id = self.ie.import_project(
                    project_json, dry_run=self.dry_run)

            if import_id and not self.dry_run:
                # Disable Auto DevOps
                self.log.info("Disabling Auto DevOps on imported project {0} (ID: {1})".format(
                    dst_path_with_namespace, import_id))
                data = {"auto_devops_enabled": False}
                # Disable shared runners
                if not self.config.shared_runners_enabled:
                    data["shared_runners_enabled"] = self.config.shared_runners_enabled
                self.projects_api.edit_project(
                    self.config.destination_host, self.config.destination_token, import_id, data)

                # Archived projects cannot be migrated
                if archived:
                    self.log.info(
                        "Unarchiving source project {0} (ID: {1})".format(path, src_id))
                    self.projects_api.unarchive_project(
                        self.config.source_host, self.config.source_token, src_id)
                self.log.info(
                    "Migrating source project {0} (ID: {1}) info".format(path, src_id))
                post_import_results = self.migrate_single_project_features(
                    project_json, import_id)
                result[dst_path_with_namespace] = post_import_results
        except (RequestException, KeyError, OverflowError) as oe:
            self.log.error("Failed to import project {0} (ID: {1}) with error:\n{2}".format(
                path, src_id, oe))
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())
        finally:
            if archived and not self.dry_run:
                self.log.info(
                    "Archiving back source project {0} (ID: {1})".format(path, src_id))
                self.projects_api.archive_project(
                    self.config.source_host, self.config.source_token, src_id)
        return result

    def migrate_single_project_features(self, project, dst_id):
        """
            Subsequent function to update project info AFTER import
        """
        project.pop("members")
        path_with_namespace = project["path_with_namespace"]
        shared_with_groups = project["shared_with_groups"]
        src_id = project["id"]
        results = {}

        results["id"] = dst_id

        # Shared with groups
        results["shared_with_groups"] = self.projects.add_shared_groups(
            dst_id, path_with_namespace, shared_with_groups)

        # Environments
        results["environments"] = self.environments.migrate_project_environments(
            src_id, dst_id, path_with_namespace)

        # CI/CD Variables
        results["variables"] = self.variables.migrate_gitlab_cicd_variables(
            src_id, dst_id, path_with_namespace, "projects")

        # Push Rules
        results["push_rules"] = self.pushrules.migrate_push_rules(
            src_id, dst_id, path_with_namespace)

        # Merge Request Approvals
        results["project_level_mr_approvals"] = self.mr_approvals.migrate_project_level_mr_approvals(
            src_id, dst_id, path_with_namespace)

        # Deploy Keys
        results["deploy_keys"] = self.keys.migrate_project_deploy_keys(
            src_id, dst_id, path_with_namespace)

        # Container Registries
        if self.config.source_registry and self.config.destination_registry:
            results["container_registry"] = self.registries.migrate_registries(
                src_id, dst_id, path_with_namespace)

        # Hooks (Webhooks)
        results["project_hooks"] = self.hooks.migrate_project_hooks(
            src_id, dst_id, path_with_namespace)

        self.projects.remove_import_user(dst_id)

        return results

    def migrate_jenkins_variables(self, project, new_id):
        if (ci_sources := project.get("ci_sources", None)) and self.config.ci_source_type == "jenkins":
            result = True
            for job in ci_sources.get("Jenkins", []):
                params = self.jenkins.jenkins_api.get_job_params(job)
                for param in params:
                    if self.variables.safe_add_variables(new_id, self.jenkins.transform_ci_variables(param)) is False:
                        result = False
            return result
        return None

    def migrate_teamcity_variables(self, project, new_id):
        if (ci_sources := project.get("ci_sources", None)) and self.config.ci_source_type == "teamcity":
            result = True
            for job in ci_sources.get("TeamCity", []):
                params = self.teamcity.teamcity_api.get_build_params(job)
                for param in params["properties"]["property"]:
                    if self.variables.safe_add_variables(new_id, self.teamcity.transform_ci_variables(param)) is False:
                        result = False
            return result
        return None

    def rollback(self):
        rotate_logs()
        dry_log = get_dry_log(self.dry_run)

        # Remove groups and projects OR only empty groups
        if not self.skip_groups:
            self.log.info("{0}Removing staged groups{1} on destination".format(
                dry_log, "" if self.skip_projects else " and projects"))
            self.groups.delete_groups(
                dry_run=self.dry_run, skip_projects=self.skip_projects)

        # Remove only projects
        if not self.skip_projects:
            self.log.info(
                "{}Removing staged projects on destination".format(dry_log))
            self.projects.delete_projects(dry_run=self.dry_run)

        if not self.skip_users:
            self.log.info("{0}Removing staged users on destination (hard_delete={1})".format(
                dry_log,
                self.hard_delete))
            self.users.delete_users(
                dry_run=self.dry_run, hard_delete=self.hard_delete)

        add_post_migration_stats(self.start, log=self.log)

    def remove_all_mirrors(self):
        # if os.path.isfile("%s/data/new_ids.txt" % self.app_path):
        #     ids = []
        #     with open("%s/data/new_ids.txt" % self.app_path, "r") as f:
        #         for line in f:
        #             ids.append(int(line.split("\n")[0]))
        # else:
        ids = self.get_new_ids()
        for i in ids:
            self.mirror.remove_mirror(i, self.dry_run)

    def get_new_ids(self):
        ids = []
        staged_projects = self.projects.get_staged_projects()
        if staged_projects:
            for project_json in staged_projects:
                try:
                    self.log.debug("Searching for existing %s" %
                                   project_json["name"])
                    for proj in self.projects_api.search_for_project(self.config.destination_host,
                                                                     self.config.destination_token,
                                                                     project_json['name']):
                        if proj["name"] == project_json["name"]:

                            if "%s" % project_json["namespace"].lower(
                            ) in proj["path_with_namespace"].lower():
                                if project_json["namespace"].lower(
                                ) == proj["namespace"]["name"].lower():
                                    self.log.debug("Adding {0}/{1}".format(
                                        project_json["namespace"], project_json["name"]))
                                    # self.log.info("Migrating variables for %s" % proj["name"])
                                    ids.append(proj["id"])
                                    break
                except IOError as e:
                    self.log.error(e)
            return ids

    def mirror_staged_projects(self):
        ids = self.get_new_ids()
        staged_projects = self.projects.get_staged_projects()
        if staged_projects:
            for i in enumerate(staged_projects):
                pid = ids[i]
                project = staged_projects[i]
                self.mirror.mirror_repo(project, pid, self.dry_run)

    def check_visibility(self):
        count = 0
        if os.path.isfile("%s/data/new_ids.txt" % self.app_path):
            ids = []
            with open("%s/data/new_ids.txt" % self.app_path, "r") as f:
                for line in f:
                    ids.append(int(line.split("\n")[0]))
        else:
            ids = self.get_new_ids()
        for i in ids:
            project = self.projects_api.get_project(
                i, self.config.destination_host, self.config.destination_token).json()
            if project["visibility"] != "private":
                self.log.debug("Current destination path {0} visibility: {1}".format(
                    project["path_with_namespace"], project["visibility"]))
                count += 1
                data = {
                    "visibility": "private"
                }
                change = api.generate_put_request(
                    self.config.destination_host, self.config.destination_token, "projects/%d?visibility=private" % int(
                        i),
                    data=None)
                print(change)
        print(count)

    def get_total_migrated_count(self):
        # group_projects = api.get_count(
        # self.config.destination_host, self.config.destination_token,
        # "groups/%d/projects" % self.config.dstn_parent_id)
        subgroup_count = 0
        for group in api.list_all(self.config.destination_host, self.config.destination_token,
                                  "groups/%d/subgroups" % self.config.dstn_parent_id):
            count = api.get_count(
                self.config.destination_host, self.config.destination_token, "groups/%d/projects" % group["id"])
            sub_count = 0
            if group.get("child_ids", None) is not None:
                for child_id in group["child_ids"]:
                    sub_count += api.get_count(self.config.destination_host,
                                               self.config.destination_token, "groups/%d/projects" % child_id)
            subgroup_count += count
        # return subgroup_count + group_projects
        self.log.inf(
            "Total count of migrated projects: {}".format(subgroup_count))

    def stage_unimported_projects(self):
        ids = []
        with open("{}/data/unimported_projects.txt".format(self.app_path), "r") as f:
            unimported_projects = f.read()
        available_projects = self.projects.get_projects()
        rewritten_projects = {}
        for i in enumerate(available_projects):
            new_obj = available_projects[i]
            id_num = available_projects[i]["path"]
            rewritten_projects[id_num] = new_obj

        unimported_projects = unimported_projects.split("\n")
        for up in unimported_projects:
            if up is not None and up:
                if rewritten_projects.get(up.split("/")[1], None) is not None:
                    ids.append(rewritten_projects.get(up.split("/")[1])["id"])
        if ids is not None and ids:
            pcli = ProjectStageCLI()
            pcli.stage_data(ids, self.dry_run)
