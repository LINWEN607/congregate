"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2022 - GitLab
"""

import os
import json
import xml.dom.minidom
import sys
from time import time
from traceback import print_exc
from requests.exceptions import RequestException

from gitlab_ps_utils import json_utils, string_utils, dict_utils, misc_utils

import congregate.helpers.migrate_utils as mig_utils
from congregate.helpers.utils import rotate_logs, is_dot_com
from congregate.helpers.reporting import Reporting
from congregate.helpers.jobtemplategenerator import JobTemplateGenerator
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
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.gitlab.merge_request_approvals import MergeRequestApprovalsClient
from congregate.migration.gitlab.registries import RegistryClient
from congregate.migration.gitlab.keys import KeysClient
from congregate.migration.gitlab.hooks import HooksClient
from congregate.migration.gitlab.clusters import ClustersClient
from congregate.migration.gitlab.environments import EnvironmentsClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.external_import import ImportClient
from congregate.migration.jenkins.base import JenkinsClient
from congregate.migration.teamcity.base import TeamcityClient
from congregate.migration.bitbucket.repos import ReposClient as BBSReposClient
from congregate.migration.github.repos import ReposClient
from congregate.migration.gitlab.packages import PackagesClient


class MigrateClient(BaseClass):
    def __init__(
        self,
        dry_run=True,
        processes=None,
        only_post_migration_info=False,
        start=time(),
        skip_users=False,
        remove_members=False,
        hard_delete=False,
        stream_groups=False,
        skip_groups=False,
        skip_projects=False,
        skip_group_export=False,
        skip_group_import=False,
        skip_project_export=False,
        skip_project_import=False,
        subgroups_only=False,
        scm_source=None,
        reg_dry_run=False,
        group_structure=False
    ):
        self.ie = ImportExportClient()
        self.variables = VariablesClient()
        self.users = UsersClient()
        self.users_api = UsersApi()
        self.groups = GroupsClient()
        self.groups_api = GroupsApi()
        self.projects = ProjectsClient()
        self.projects_api = ProjectsApi()
        self.project_repository_api = ProjectRepositoryApi()
        self.namespaces_api = NamespacesApi()
        self.instance_api = InstanceApi()
        self.mr_approvals = MergeRequestApprovalsClient()
        self.registries = RegistryClient(
            reg_dry_run=reg_dry_run
        )
        self.packages = PackagesClient()
        self.keys = KeysClient()
        self.hooks = HooksClient()
        self.clusters = ClustersClient()
        self.environments = EnvironmentsClient()
        self.branches = BranchesClient()
        self.ext_import = ImportClient()
        super().__init__()
        self.bbs_repos_client = BBSReposClient()
        self.job_template = JobTemplateGenerator()
        self.dry_run = dry_run
        self.processes = processes
        self.only_post_migration_info = only_post_migration_info
        self.start = start
        self.skip_users = skip_users
        self.stream_groups = stream_groups
        self.remove_members = remove_members
        self.hard_delete = hard_delete
        self.skip_groups = skip_groups
        self.skip_projects = skip_projects
        self.skip_group_export = skip_group_export
        self.skip_group_import = skip_group_import
        self.skip_project_export = skip_project_export
        self.skip_project_import = skip_project_import
        self.subgroups_only = subgroups_only
        self.scm_source = scm_source
        self.group_structure = group_structure

    def migrate(self):
        self.log.info(
            f"{misc_utils.get_dry_log(self.dry_run)}Migrating data from {self.config.source_host} ({self.config.source_type}) to "
            f"{self.config.destination_host}"
        )

        # Dry-run and log cleanup
        if self.dry_run:
            mig_utils.clean_data(dry_run=False, files=[
                f"{self.app_path}/data/results/dry_run_user_migration.json",
                f"{self.app_path}/data/results/dry_run_group_migration.json",
                f"{self.app_path}/data/results/dry_run_project_migration.json"])
        rotate_logs()

        if self.config.source_type == "gitlab":
            self.migrate_from_gitlab()
        elif self.config.source_type == "bitbucket server":
            self.migrate_from_bitbucket_server()
        elif self.config.source_type == "github" or self.config.list_multiple_source_config("github_source"):
            self.migrate_from_github()
        else:
            self.log.warning(
                f"Configuration (data/congregate.conf) src_type {self.config.source_type} not supported")
        mig_utils.add_post_migration_stats(self.start, log=self.log)
        self.log.warning(
            f"{misc_utils.get_dry_log(self.dry_run)}Completed migrating from {self.config.source_host} to {self.config.destination_host}")

    def validate_groups_and_projects(self, staged, are_projects=False):
        if dupes := mig_utils.get_duplicate_paths(
                staged, are_projects=are_projects):
            self.log.warning("Duplicate {} paths:\n{}".format(
                "project" if are_projects else "group", "\n".join(d for d in dupes)))
        if not are_projects:
            # Temp bug fix: Group names must be 2+ characters long
            if invalid_group_names := [
                    g for g in staged if len(g["name"]) < 2]:
                self.log.warning("Invalid group names:\n{}".format(
                    "\n".join(i for i in invalid_group_names)))

    def migrate_from_gitlab(self):
        # Users
        self.migrate_user_info()

        # Groups
        self.migrate_group_info()

        # Projects
        self.migrate_project_info()

        # Instance hooks
        self.hooks.migrate_instance_hooks(dry_run=self.dry_run)

        # Instance clusters
        self.clusters.migrate_instance_clusters(dry_run=self.dry_run)

        # Remove import user from parent group to avoid inheritance
        # (self-managed only)
        if not self.dry_run and self.config.dstn_parent_id and not is_dot_com(
                self.config.destination_host):
            self.remove_import_user(
                self.config.dstn_parent_id, gl_type="group")

    def migrate_from_github(self):
        dry_log = misc_utils.get_dry_log(self.dry_run)

        # Migrate users
        self.migrate_user_info()

        # Migrate GH orgs as groups
        self.migrate_github_org_info(dry_log)

        # Migrate GH repos as projects
        self.migrate_github_repo_info(dry_log)

    def migrate_github_org_info(self, dry_log):
        staged_groups = mig_utils.get_staged_groups()
        if staged_groups and not self.skip_group_import and not self.group_structure and not self.config.wave_spreadsheet_path:
            self.validate_groups_and_projects(staged_groups)
            self.log.info(
                f"{dry_log}Migrating GitHub orgs as GitLab groups")
            results = list(r for r in self.multi.start_multi_process(
                self.migrate_external_group, staged_groups, processes=self.processes, nestable=True))
            self.are_results(results, "group", "import")
            results.append(mig_utils.get_results(results))
            self.log.info(
                f"### {dry_log}GitHub orgs migration result ###\n{json_utils.json_pretty(results)}")
            mig_utils.write_results_to_file(
                results, result_type="group", log=self.log)
        elif self.group_structure:
            self.log.info(
                "Skipping GitHub orgs migration and relying on GitHub importer to create missing GitLab sub-group layers")
        elif self.config.wave_spreadsheet_path:
            self.log.warning(
                "Skipping GitHub orgs migration. Not supported when 'wave_spreadsheet_path' is configured")
        else:
            self.log.warning("SKIP: No GitHub orgs staged for migration")

    def migrate_github_repo_info(self, dry_log):
        import_results = None
        staged_projects = mig_utils.get_staged_projects()
        if staged_projects and not self.skip_project_import:
            self.validate_groups_and_projects(
                staged_projects, are_projects=True)
            if user_projects := mig_utils.get_staged_user_projects(
                    staged_projects):
                self.log.warning("User repos staged:\n{}".format(
                    "\n".join(u for u in user_projects)))
            self.log.info("Importing repos from GitHub")
            import_results = list(ir for ir in self.multi.start_multi_process(
                self.import_github_repo, staged_projects, processes=self.processes, nestable=True))

            self.are_results(import_results, "project", "import")
            # append Total : Successful count of project imports
            import_results.append(mig_utils.get_results(import_results))
            self.log.info(
                f"### {dry_log}GitHub repos import result ###\n{json_utils.json_pretty(import_results)}")
            mig_utils.write_results_to_file(import_results, log=self.log)
        else:
            self.log.warning("SKIP: No GitHub repos staged for migration")

        # After all is said and done, run our reporting with the
        # staged_projects and results
        if staged_projects and import_results:
            self.create_issue_reporting(staged_projects, import_results)

    def check_reporting_requirements(self):
        '''
        Return true if congregate.conf is correct, log an error if not.

        '''
        if self.config.reporting:
            if all([
                self.config.reporting,
                self.config.reporting.get("post_migration_issues"),
                self.config.reporting.get("pmi_project_id")
            ]):
                self.log.info(
                    "Successfully got reporting config from congregate.conf. Proceeding to make our issues.")
                return True
            self.log.error(
                "Couldn't find a required REPORTING config in [DESTINATION] section of congregate.conf.\n"
                "Issues will not be created."
            )

    def create_issue_reporting(self, staged_projects, import_results):
        '''
        Use the Reporting class to create/update whatever issues are in the congregate.conf for a given staged_projects
        and import_results.

        '''

        if self.check_reporting_requirements():
            if report := Reporting(
                reporting_project_id=self.config.reporting['pmi_project_id'],
                dry_run=self.dry_run
            ):
                report.handle_creating_issues(staged_projects, import_results)
            else:
                self.log.warning(
                    "REPORTING: Failed to instantiate the reporting module")

    def import_github_repo(self, project):
        dstn_pwn, tn = mig_utils.get_stage_wave_paths(project)
        host = self.config.destination_host
        token = self.config.destination_token
        project_id = None
        if self.group_structure or self.groups.find_group_id_by_path(host, token, tn):
            # Already imported
            if dst_pid := self.projects.find_project_by_path(host, token, dstn_pwn):
                result = self.ext_import.get_result_data(
                    dstn_pwn, {"id": dst_pid})
                if self.only_post_migration_info:
                    result = self.handle_gh_post_migration(
                        result, dstn_pwn, project, dst_pid)
                else:
                    self.log.warning(
                        f"Skipping import. Repo {dstn_pwn} has already been imported")
            # New import
            else:
                gh_host, gh_token = self.get_host_and_token()
                result = self.ext_import.trigger_import_from_ghe(
                    project, dstn_pwn, tn, gh_host, gh_token, dry_run=self.dry_run)
                result_response = result[dstn_pwn]["response"]
                if (isinstance(result_response, dict)) and (project_id := result_response.get("id")):
                    full_path = result_response.get("full_path").strip("/")
                    success = self.ext_import.wait_for_project_to_import(
                        full_path)
                    if success:
                        result = self.handle_gh_post_migration(
                            result, dstn_pwn, project, project_id)
                    else:
                        result = self.ext_import.get_failed_result(
                            dstn_pwn,
                            data={"error": "Import failed or time limit exceeded. Unable to execute post migration phase"})
                else:
                    result = self.ext_import.get_failed_result(
                        dstn_pwn,
                        data={"error": f"Failed import, with response/payload {result_response}. Unable to execute post migration phase"})
            # Repo import status
            if dst_pid or project_id:
                result[dstn_pwn]["import_status"] = self.ext_import.get_external_repo_import_status(
                    host, token, dst_pid or project_id)
        else:
            log = f"Target namespace {tn} does not exist"
            self.log.warning("Skipping import. " + log +
                             f" for {project['path']}")
            result = self.ext_import.get_result_data(dstn_pwn, {
                "error": log
            })
        return result

    def get_host_and_token(self):
        if self.scm_source:
            for single_source in self.config.list_multiple_source_config(
                    "github_source"):
                if self.scm_source in single_source.get("src_hostname", None):
                    gh_host = single_source["src_hostname"]
                    gh_token = string_utils.deobfuscate(
                        single_source["src_access_token"])
                    self.gh_repos = ReposClient(gh_host, gh_token)
        else:
            gh_host = self.config.source_host
            gh_token = self.config.source_token
            self.gh_repos = ReposClient(gh_host, gh_token)

        return gh_host, gh_token

    def handle_gh_post_migration(self, result, path_with_namespace, project, pid):
        members = project.pop("members")
        result[path_with_namespace]["members"] = self.projects.add_members_to_destination_project(
            self.config.destination_host, self.config.destination_token, pid, members)

        # Disable Shared CI
        self.disable_shared_ci(path_with_namespace, pid)

        # Migrate any external CI data
        self.handle_ext_ci_src_migration(result, project, pid)

        # Add pages file to repo
        result[path_with_namespace]["is_gh_pages"] = self.add_pipeline_for_github_pages(
            pid)

        # Add protected branch
        result[path_with_namespace]["project_level_protected_branch"] = (
            self.gh_repos.migrate_gh_project_protected_branch(pid, project)
        )

        # Add repo level MR rules
        result[path_with_namespace]["project_level_mr_approvals"] = (
            self.gh_repos.migrate_gh_project_level_mr_approvals(pid, project)
        )

        # Archive migrated repos on destination
        result[path_with_namespace]["archived"] = self.gh_repos.archive_migrated_repo(
            pid, project)

        # Determine whether to remove all repo members
        result[path_with_namespace]["members"]["email"] = self.handle_member_retention(
            members, pid)

        # Remove import user; SKIP if removing all other members
        if not self.remove_members:
            self.remove_import_user(pid)

        return result

    def handle_ext_ci_src_migration(self, result, project, project_id):
        if jenkins_configs := self.config.list_ci_source_config(
                "jenkins_ci_source"):
            for jc in jenkins_configs:
                jenkins_client = (
                    JenkinsClient(
                        jc["jenkins_ci_src_hostname"],
                        jc["jenkins_ci_src_username"],
                        string_utils.deobfuscate(
                            jc["jenkins_ci_src_access_token"]
                        )
                    )
                )
                result[project["path_with_namespace"]]["jenkins_variables"] = (
                    self.migrate_jenkins_variables(
                        project,
                        project_id,
                        jenkins_client,
                        jc["jenkins_ci_src_hostname"]
                    )
                )
                result[project["path_with_namespace"]]["jenkins_config_xml"] = (
                    self.migrate_jenkins_config_xml(
                        project,
                        project_id,
                        jenkins_client
                    )
                )
        if teamcity_configs := self.config.list_ci_source_config(
                "teamcity_ci_source"):
            for tc in teamcity_configs:
                tc_client = TeamcityClient(tc["tc_ci_src_hostname"], tc["tc_ci_src_username"], string_utils.deobfuscate(
                    tc["tc_ci_src_access_token"]))
                result[project["path_with_namespace"]]["teamcity_variables"] = (
                    self.migrate_teamcity_variables(
                        project,
                        project_id,
                        tc_client,
                        tc["tc_ci_src_hostname"]
                    )
                )
                result[project["path_with_namespace"]]["teamcity_config_xml"] = (
                    self.migrate_teamcity_build_config(
                        project, project_id, tc_client)
                )

    def handle_member_retention(self, members, dst_id, group=False):
        status = "retained"
        if self.remove_members:
            if group:
                members = misc_utils.safe_json_response(self.groups_api.get_all_group_members(
                    dst_id, self.config.destination_host, self.config.destination_token)) or []
            # Leave the import user as the only (Owner) member
            members = [m for m in members if m["id"]
                       != self.config.import_user_id]
            for m in members:
                # Remove GitLab group or GitHub repo member
                uid = m["id"] if group else m["user_id"]
                if group:
                    resp = self.groups_api.remove_member(
                        dst_id, uid, self.config.destination_host, self.config.destination_token)
                else:
                    resp = self.projects_api.remove_member(
                        dst_id, uid, self.config.destination_host, self.config.destination_token)
                if not resp or resp.status_code != 204:
                    status = "partial"
                    self.log.error(
                        f"Failed to remove {'group' if group else 'project'} {dst_id} member {uid}:\n{resp}")
            status = "partial" if status == "partial" else "removed"
        return status

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
        for branch in self.project_repository_api.get_all_project_repository_branches(
                project_id,
                self.config.destination_host,
                self.config.destination_token):
            if isinstance(branch, dict):
                if branch["name"] == "gh-pages":
                    is_result = True
                    self.project_repository_api.create_repo_file(
                        self.config.destination_host, self.config.destination_token,
                        project_id, ".gitlab-ci.yml", data)
        return is_result

    def migrate_from_bitbucket_server(self):
        dry_log = misc_utils.get_dry_log(self.dry_run)

        # Migrate users
        self.migrate_user_info()

        # Migrate BB projects as GL groups
        self.migrate_bitbucket_server_project_info(dry_log)

        # Migrate BB repos as GL projects
        self.migrate_bitbucket_server_repo_info(dry_log)

    def migrate_bitbucket_server_project_info(self, dry_log):
        staged_groups = mig_utils.get_staged_groups()
        if staged_groups and not self.skip_group_import and not self.group_structure and not self.config.wave_spreadsheet_path:
            self.validate_groups_and_projects(staged_groups)
            self.log.info(
                f"{dry_log}Migrating BitBucket projects as GitLab groups")
            results = list(r for r in self.multi.start_multi_process(
                self.migrate_external_group, staged_groups, processes=self.processes, nestable=True))

            self.are_results(results, "group", "import")

            results.append(mig_utils.get_results(results))
            self.log.info(
                f"### {dry_log}BitBucket projects migration result ###\n{json_utils.json_pretty(results)}")
            mig_utils.write_results_to_file(
                results, result_type="group", log=self.log)
        # Allow BitBucket Server importer to create missing sub-group layers on repo import
        elif self.group_structure:
            self.log.info(
                "Skipping BitBucket projects migration and relying on BitBucket Server importer to create missing GitLab sub-group layers")
        elif self.config.wave_spreadsheet_path:
            self.log.warning(
                "Skipping BitBucket projects migration. Not supported when 'wave_spreadsheet_path' is configured")
        else:
            self.log.warning(
                "SKIP: No BitBucket projects staged for migration")

    def migrate_bitbucket_server_repo_info(self, dry_log):
        staged_projects = mig_utils.get_staged_projects()
        if staged_projects and not self.skip_project_import:
            self.validate_groups_and_projects(
                staged_projects, are_projects=True)
            if user_projects := mig_utils.get_staged_user_projects(
                    staged_projects):
                self.log.warning("User repos staged:\n{}".format(
                    "\n".join(u for u in user_projects)))
            self.log.info("Importing BitBucket repos")
            import_results = list(ir for ir in self.multi.start_multi_process(
                self.import_bitbucket_repo, staged_projects, processes=self.processes, nestable=True))

            self.are_results(import_results, "project", "import")

            # append Total : Successful count of project imports
            import_results.append(mig_utils.get_results(import_results))
            self.log.info(
                f"### {dry_log}BitBucket repos import result ###\n{json_utils.json_pretty(import_results)}")
            mig_utils.write_results_to_file(import_results, log=self.log)
        else:
            self.log.warning(
                "SKIP: No BitBucket repos staged for migration")

    def migrate_external_group(self, group):
        result = False
        members = group.pop("members")
        group["full_path"] = mig_utils.get_full_path_with_parent_namespace(
            group["full_path"]).lower()
        if group.get("path"):
            group["path"] = group["path"].lower()
        group["parent_id"] = self.config.dstn_parent_id
        group_id = None
        group["description"] = group.get("description") or ""
        host = self.config.destination_host
        token = self.config.destination_token
        if group_id := self.groups.find_group_id_by_path(host, token, group["full_path"]):
            self.log.info(
                f"{group['full_path']} ({group_id}) found. Skipping import. Adding members")
        if not self.dry_run:
            result = {}
            if not group_id:
                resp = misc_utils.safe_json_response(
                    self.groups_api.create_group(host, token, group))
                is_error, resp = misc_utils.is_error_message_present(resp)
                if resp and not is_error:
                    group_id = resp.get("id")
                    result["response"] = resp
                else:
                    self.log.error(
                        f"Unable to create group {group['full_path']} due to: {result}")
            if group_id:
                if not self.remove_members:
                    result["members"] = self.groups.add_members_to_destination_group(
                        host, token, group_id, members)
                self.remove_import_user(group_id, gl_type="group")
        return {
            group["full_path"]: result
        }

    def import_bitbucket_repo(self, project):
        pwn = project.get("path_with_namespace")
        dstn_pwn, tn = mig_utils.get_stage_wave_paths(project)
        host = self.config.destination_host
        token = self.config.destination_token
        project_id = None
        if self.group_structure or self.groups.find_group_id_by_path(host, token, tn):
            # Already imported
            if dst_pid := self.projects.find_project_by_path(host, token, dstn_pwn):
                result = self.ext_import.get_result_data(
                    dstn_pwn, {"id": dst_pid})
                if self.only_post_migration_info:
                    result = self.handle_bb_post_migration(
                        result, dstn_pwn, project, dst_pid)
                else:
                    self.log.warning(
                        f"Skipping import. Repo {dstn_pwn} has already been imported")
            # New import
            else:
                result = self.ext_import.trigger_import_from_bb_server(
                    pwn, dstn_pwn, tn, dry_run=self.dry_run)
                result_response = result[dstn_pwn]["response"]
                if (isinstance(result_response, dict)) and (project_id := result_response.get("id")):
                    full_path = result_response.get("full_path").strip("/")
                    success = self.ext_import.wait_for_project_to_import(
                        full_path)
                    if success:
                        result = self.handle_bb_post_migration(
                            result, dstn_pwn, project, project_id)
                    else:
                        result = self.ext_import.get_failed_result(
                            dstn_pwn,
                            data={"error": "Import failed or time limit exceeded. Unable to execute post migration phase"})
                else:
                    result = self.ext_import.get_failed_result(
                        dstn_pwn,
                        data={"error": f"Failed import, with response {result_response}. Unable to execute post migration phase"})
            # Repo import status
            if dst_pid or project_id:
                result[dstn_pwn]["import_status"] = self.ext_import.get_external_repo_import_status(
                    host, token, dst_pid or project_id)
        else:
            log = f"Target namespace {tn} does not exist"
            self.log.warning("Skipping import. " + log +
                             f" for {project['path']}")
            result = self.ext_import.get_result_data(dstn_pwn, {
                "error": log
            })
        return result

    def handle_bb_post_migration(self, result, path_with_namespace, project, pid):
        members = project.pop("members")
        if not self.remove_members:
            result[path_with_namespace]["members"] = self.projects.add_members_to_destination_project(
                self.config.destination_host, self.config.destination_token, pid, members)

        # Set default branch
        self.branches.set_branch(
            path_with_namespace, pid, project.get("default_branch"))

        # Set branch permissions
        self.bbs_repos_client.migrate_permissions(
            project, pid)

        # Correcting bug where group's description is persisted to
        # project's description
        self.bbs_repos_client.correct_repo_description(
            project, pid)

        # Remove import user; SKIP if removing all other members
        if not self.remove_members:
            self.remove_import_user(pid)
        return result

    def are_results(self, results, var, stage):
        if not results:
            self.log.warning(
                f"Results from {var} {stage} returned as empty. Aborting.")
            mig_utils.add_post_migration_stats(self.start, log=self.log)
            sys.exit(os.EX_OK)

    def migrate_user_info(self):
        staged_users = mig_utils.get_staged_users()
        if staged_users:
            if not self.skip_users:
                self.log.info("{}Migrating user info".format(
                    misc_utils.get_dry_log(self.dry_run)))
                staged = self.users.handle_users_not_found(
                    "staged_users",
                    self.users.search_for_staged_users()[0],
                    keep=not self.only_post_migration_info
                )
                new_users = list(nu for nu in self.multi.start_multi_process(
                    self.handle_user_creation, staged, self.processes))
                self.are_results(new_users, "user", "creation")
                formatted_users = {}
                for nu in new_users:
                    formatted_users[nu["email"]] = nu
                new_users.append(mig_utils.get_results(new_users))
                self.log.info("### {0}User creation results ###\n{1}"
                              .format(misc_utils.get_dry_log(self.dry_run), json_utils.json_pretty(new_users)))
                mig_utils.write_results_to_file(
                    formatted_users, result_type="user", log=self.log)
                if self.dry_run and not self.only_post_migration_info:
                    self.log.info(
                        "DRY-RUN: Outputing various USER migration data to dry_run_user_migration.json")
                    mig_utils.migration_dry_run("user", list(self.multi.start_multi_process(
                        self.users.generate_user_data, staged_users, self.processes)))
            else:
                self.log.info(
                    "SKIP: Assuming staged users are already migrated")
        else:
            self.log.warning("SKIP: No users staged for migration")

    def handle_user_creation(self, user):
        """
            This is called when importing staged_users.json.
            Inactive users will be skipped if we do NOT 'keep_inactive_users'.

            :param user: Each iterable called is a user from the staged_users.json file
            :return:
        """
        response = None
        state = user.get("state").lower()
        email = user.get("email")
        name = user.get("name")
        username = user.get("username")
        new_user = {
            "email": email,
            "id": None
        }
        old_user = {
            "email": email,
            "id": user.get("id")
        }
        try:
            if not self.only_post_migration_info:
                if (state == "active" or (state in self.INACTIVE and self.config.keep_inactive_users)) and all(
                        v for v in [name, username, email]):
                    user_data = self.users.generate_user_data(user)
                    self.log.info(
                        f"{misc_utils.get_dry_log(self.dry_run)}Attempting to create user {email}")
                    response = self.users_api.create_user(
                        self.config.destination_host,
                        self.config.destination_token,
                        user_data
                    ) if not self.dry_run else None
                else:
                    self.log.info(
                        f"SKIP: Not migrating {state} user:\n{json_utils.json_pretty(user)}")
                if response is not None:
                    # NOTE: Persist 'inactive' user state regardless of domain
                    # and creation status.
                    if user_data.get("state").lower() in self.INACTIVE:
                        self.users.block_user(user_data)
                    new_user = self.users.handle_user_creation_status(
                        response, user_data)
            if not self.dry_run and self.config.source_type == "gitlab":
                if new_user:
                    found_user = new_user if new_user.get(
                        "id") is not None else mig_utils.find_user_by_email_comparison_without_id(email)
                    new_user["id"] = found_user.get(
                        "id") if found_user else None
                    if found_user:
                        # Migrate SSH keys
                        self.keys.migrate_user_ssh_keys(old_user, new_user)
                        # Migrate GPG keys
                        self.keys.migrate_user_gpg_keys(old_user, new_user)
                else:
                    self.log.warning(
                        f"Could not create user. User may exist with a different primary email. Check previous logs warnings. Userdata follows:\n{user_data}")
                    # Return the "original" new_user setting
                    return {
                        "email": email,
                        "id": None
                    }
        except RequestException as e:
            self.log.error(
                f"Failed to create user {user_data}, with error:\n{e}")
        except Exception as e:
            self.log.error(f"Could not get response text/JSON. Error was {e}")
            self.log.error(print_exc(e))
        return new_user

    def migrate_group_info(self):
        staged_groups = mig_utils.get_staged_groups()
        staged_top_groups = [
            g for g in staged_groups if mig_utils.is_top_level_group(g)]
        staged_subgroups = [
            g for g in staged_groups if not mig_utils.is_top_level_group(g)]
        dry_log = misc_utils.get_dry_log(self.dry_run)
        if staged_top_groups or (staged_subgroups and self.subgroups_only):
            self.validate_groups_and_projects(staged_groups)
            if self.stream_groups:
                self.stream_import_groups(
                    staged_top_groups, staged_subgroups, dry_log)
            else:
                self.export_import_groups(
                    staged_top_groups, staged_subgroups, dry_log)
        else:
            self.log.warning(
                "SKIP: No groups staged for migration. Migrating ONLY sub-groups without '--subgroups-only'?")

    def export_import_groups(self, staged_top_groups, staged_subgroups, dry_log):
        if not self.skip_group_export:
            self.log.info(f"{dry_log}Exporting groups")
            export_results = list(er for er in self.multi.start_multi_process(
                self.handle_exporting_groups,
                staged_subgroups if self.subgroups_only else staged_top_groups,
                processes=self.processes
            ))

            self.are_results(export_results, "group", "export")

            # Create list of groups that failed export
            if failed := mig_utils.get_failed_export_from_results(
                    export_results):
                self.log.warning(
                    f"SKIP: Groups that failed to export or already exist on destination:\n{json_utils.json_pretty(failed)}")

            # Append total count of groups exported
            export_results.append(mig_utils.get_results(export_results))
            self.log.info(
                f"### {dry_log}Group export results ###\n{json_utils.json_pretty(export_results)}")

            # Filter out the failed ones
            staged_top_groups = mig_utils.get_staged_groups_without_failed_export(
                staged_top_groups, failed)
        else:
            self.log.info(
                "SKIP: Assuming staged groups are already exported")
        if not self.skip_group_import:
            self.log.info(f"{dry_log}Importing groups")
            import_results = list(ir for ir in self.multi.start_multi_process(
                self.handle_importing_groups,
                staged_subgroups if self.subgroups_only else staged_top_groups,
                processes=self.processes
            ))

            # Migrate sub-group info
            if staged_subgroups:
                import_results += list(ir for ir in self.multi.start_multi_process(
                    self.migrate_subgroup_info, staged_subgroups, processes=self.processes))

            self.are_results(import_results, "group", "import")

            # Append Total : Successful count of group migrations
            import_results.append(mig_utils.get_results(import_results))
            self.log.info(
                f"### {dry_log}Group import results ###\n{json_utils.json_pretty(import_results)}")
            mig_utils.write_results_to_file(
                import_results, result_type="group", log=self.log)
        else:
            self.log.info(
                "SKIP: Assuming staged groups will be later imported")

    def stream_import_groups(self, staged_top_groups, staged_subgroups, dry_log):
        self.log.info(f"{dry_log}Importing groups in bulk")

        # Only import relevant groups, the rest will unpack
        import_results = self.import_groups(
            staged_subgroups if self.subgroups_only else staged_top_groups, dry_log)

        if not self.dry_run:
            # Match full_path against ALL staged groups
            # Migrate single group features if import "finished" or group already exists
            for ir in import_results:
                ex_full_path = next(iter(ir))
                full_path = ir.get("source_full_path") or ex_full_path
                status = ir.get("status")
                if status == "finished" or ir.get(ex_full_path):
                    src_gid = next((g["id"] for g in (
                        staged_top_groups + staged_subgroups) if g["full_path"] == full_path), None)
                    dst_gid = ir.get("namespace_id") or ex_full_path
                    self.migrate_single_group_features(
                        src_gid, dst_gid, full_path)
                else:
                    self.log.error(
                        f"Cannot migrate {full_path} single group features. Import status: {status}")

        self.are_results(import_results, "group", "import")

        # Append Total : Successful count of group migrations
        import_results.append(mig_utils.get_results(import_results))
        self.log.info(
            f"### {dry_log}Group bulk import results ###\n{json_utils.json_pretty(import_results)}")
        mig_utils.write_results_to_file(
            import_results, result_type="group", log=self.log)

    def import_groups(self, groups, dry_log):
        data = {
            "configuration": {
                "url": self.config.source_host,
                "access_token": self.config.source_token
            },
            "entities": []
        }
        host = self.config.destination_host
        token = self.config.destination_token
        imported = False
        try:
            # Prepare group entities and current result for destination
            data["entities"], result = self.groups.find_and_stage_group_bulk_entities(
                groups)
            self.log.info(
                f"{dry_log}Start bulk group import, with payload:\n{json_utils.json_pretty(data['entities'])} and destination state:\n{json_utils.json_pretty(result)}")

            if data["entities"] and not self.dry_run:
                bulk_import_resp = self.groups_api.bulk_group_import(
                    host, token, data=data)
                if bulk_import_resp.status_code != 201:
                    self.log.error(
                        f"Failed to trigger group bulk import, with response:\n{bulk_import_resp} - {bulk_import_resp.text}")
                else:
                    bid = misc_utils.safe_json_response(
                        bulk_import_resp).get("id")
                    imported = self.ie.wait_for_bulk_group_import(
                        bulk_import_resp, bid)
            if imported:
                result = list(self.groups_api.get_all_bulk_group_import_entities(
                    host, token, bid))
        except (RequestException, KeyError, OverflowError) as oe:
            self.log.error(
                f"Failed to import bulk group groups with error:\n{oe}")
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())
        return result

    def handle_exporting_groups(self, group):
        full_path = group["full_path"]
        gid = group["id"]
        dry_log = misc_utils.get_dry_log(self.dry_run)
        filename = mig_utils.get_export_filename_from_namespace_and_name(
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
        try:
            if isinstance(group, str):
                group = json.loads(group)
            full_path = group["full_path"]
            src_gid = group["id"]
            full_path_with_parent_namespace = mig_utils.get_full_path_with_parent_namespace(
                full_path)
            filename = mig_utils.get_export_filename_from_namespace_and_name(
                full_path)
            result = {
                full_path_with_parent_namespace: False
            }
            import_id = None
            dry_log = misc_utils.get_dry_log(self.dry_run)
            dst_grp = self.groups.find_group_by_path(
                self.config.destination_host, self.config.destination_token, full_path_with_parent_namespace)
            dst_gid = dst_grp.get("id") if dst_grp else None
            if dst_gid:
                self.log.info(
                    f"{dry_log}Group {full_path} (ID: {dst_gid}) already exists on destination")
                result[full_path_with_parent_namespace] = dst_gid
                if self.only_post_migration_info and not self.dry_run:
                    import_id = dst_gid
                else:
                    result[full_path_with_parent_namespace] = dst_gid
            else:
                self.log.info(
                    f"{dry_log}Group {full_path_with_parent_namespace} NOT found on destination, importing...")
                imported = self.ie.import_group(
                    group,
                    full_path_with_parent_namespace,
                    filename,
                    dry_run=self.dry_run,
                    subgroups_only=self.subgroups_only
                )
                # In place of checking the import status
                if not self.dry_run and imported:
                    import_id = self.ie.wait_for_group_import(
                        full_path_with_parent_namespace).get("id")
            if import_id and not self.dry_run:
                result[full_path_with_parent_namespace] = self.migrate_single_group_features(
                    src_gid, import_id, full_path)
        except (RequestException, KeyError, OverflowError) as oe:
            self.log.error(
                f"Failed to import group {full_path} (ID: {src_gid}) as {filename} with error:\n{oe}")
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())
        return result

    def migrate_subgroup_info(self, subgroup):
        try:
            if isinstance(subgroup, str):
                subgroup = json.loads(subgroup)
            full_path = subgroup["full_path"]
            src_gid = subgroup["id"]
            full_path_with_parent_namespace = mig_utils.get_full_path_with_parent_namespace(
                full_path)
            result = {
                full_path_with_parent_namespace: False
            }
            self.log.info(
                f"Searching on destination for sub-group {full_path_with_parent_namespace}")
            if self.dry_run:
                dst_gid = self.groups.find_group_id_by_path(
                    self.config.destination_host, self.config.destination_token, full_path_with_parent_namespace)
            else:
                dst_grp = self.ie.wait_for_group_import(
                    full_path_with_parent_namespace)
                dst_gid = dst_grp.get("id") if dst_grp else None
            if dst_gid:
                self.log.info(
                    f"{misc_utils.get_dry_log(self.dry_run)}Sub-group {full_path} (ID: {dst_gid}) found on destination")
                if not self.dry_run:
                    result[full_path_with_parent_namespace] = self.migrate_single_group_features(
                        src_gid, dst_gid, full_path)
            elif not self.dry_run:
                self.log.warning(
                    f"Sub-group {full_path_with_parent_namespace} NOT found on destination")
        except (RequestException, KeyError, OverflowError) as oe:
            self.log.error(
                f"Failed to migrate sub-group {full_path} (ID: {src_gid}) info with error:\n{oe}")
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())
        return result

    def migrate_single_group_features(self, src_gid, dst_gid, full_path):
        results = {}
        results["id"] = dst_gid

        # CI/CD Variables
        results["cicd_variables"] = self.variables.migrate_cicd_variables(
            src_gid, dst_gid, full_path, "group", src_gid)

        # Clusters
        results["clusters"] = self.clusters.migrate_group_clusters(
            src_gid, dst_gid, full_path)

        if self.config.source_tier not in ["core", "free"]:
            # Hooks (Webhooks)
            results["hooks"] = self.hooks.migrate_group_hooks(
                src_gid, dst_gid, full_path)

        # Determine whether to remove all group members
        results["members"] = self.handle_member_retention(
            [], dst_gid, group=True)

        # Remove import user; SKIP if removing all other members
        if not self.remove_members:
            self.remove_import_user(dst_gid, gl_type="group")

        return results

    def migrate_project_info(self):
        staged_projects = mig_utils.get_staged_projects()
        dry_log = misc_utils.get_dry_log(self.dry_run)
        if staged_projects:
            self.validate_groups_and_projects(
                staged_projects, are_projects=True)
            if user_projects := mig_utils.get_staged_user_projects(
                    staged_projects):
                self.log.warning("User projects staged:\n{}".format(
                    "\n".join(u for u in user_projects)))
            if not self.skip_project_export:
                self.log.info("{}Exporting projects".format(dry_log))
                export_results = list(er for er in self.multi.start_multi_process(
                    self.handle_exporting_projects, staged_projects, processes=self.processes))

                self.are_results(export_results, "project", "export")

                # Create list of projects that failed export
                if failed := mig_utils.get_failed_export_from_results(
                        export_results):
                    self.log.warning("SKIP: Projects that failed to export or already exist on destination:\n{}".format(
                        json_utils.json_pretty(failed)))

                # Append total count of projects exported
                export_results.append(mig_utils.get_results(export_results))
                self.log.info("### {0}Project export results ###\n{1}"
                              .format(dry_log, json_utils.json_pretty(export_results)))

                # Filter out the failed ones
                staged_projects = mig_utils.get_staged_projects_without_failed_export(
                    staged_projects, failed)
            else:
                self.log.info(
                    "SKIP: Assuming staged projects are already exported")

            if not self.skip_project_import:
                self.log.info("{}Importing projects".format(dry_log))
                import_results = list(ir for ir in self.multi.start_multi_process(
                    self.handle_importing_projects, staged_projects, processes=self.processes))

                self.are_results(import_results, "project", "import")

                # append Total : Successful count of project imports
                import_results.append(mig_utils.get_results(import_results))
                self.log.info("### {0}Project import results ###\n{1}"
                              .format(dry_log, json_utils.json_pretty(import_results)))
                mig_utils.write_results_to_file(import_results, log=self.log)
            else:
                self.log.info(
                    "SKIP: Assuming staged projects will be later imported")
        else:
            self.log.warning("SKIP: No projects staged for migration")

    def handle_exporting_projects(self, project):
        name = project["name"]
        namespace = project["namespace"]
        pid = project["id"]
        dry_log = misc_utils.get_dry_log(self.dry_run)
        filename = mig_utils.get_export_filename_from_namespace_and_name(
            namespace, name)
        result = {
            filename: False
        }
        try:
            self.log.info(
                f"{dry_log}Exporting project {project['path_with_namespace']} (ID: {pid}) as {filename}")
            result[filename] = self.ie.export_project(
                project, dry_run=self.dry_run)
        except (IOError, RequestException) as oe:
            self.log.error(
                f"Failed to export/download project {name} (ID: {pid}) as {filename} with error:\n{oe}")
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())
        return result

    def handle_importing_projects(self, project):
        src_id = project["id"]
        archived = project["archived"]
        path = project["path_with_namespace"]
        dst_path_with_namespace = mig_utils.get_dst_path_with_namespace(
            project)
        result = {
            dst_path_with_namespace: False
        }
        import_id = None
        try:
            if isinstance(project, str):
                project = json.loads(project)
            dst_pid = self.projects.find_project_by_path(
                self.config.destination_host, self.config.destination_token, dst_path_with_namespace)
            # Certain project features cannot be migrated when archived
            if archived and not self.dry_run:
                self.log.info(
                    "Unarchiving source project {0} (ID: {1})".format(path, src_id))
                self.projects_api.unarchive_project(
                    self.config.source_host, self.config.source_token, src_id)
            if dst_pid:
                import_status = misc_utils.safe_json_response(self.projects_api.get_project_import_status(
                    self.config.destination_host, self.config.destination_token, dst_pid))
                self.log.info("Project {0} (ID: {1}) found on destination, with import status: {2}".format(
                    dst_path_with_namespace, dst_pid, import_status))
                import_id = dst_pid
                if self.dry_run:
                    result[dst_path_with_namespace] = dst_pid
            else:
                self.log.info(
                    f"{misc_utils.get_dry_log(self.dry_run)}Project {dst_path_with_namespace} NOT found on destination, importing...")
                import_id = self.ie.import_project(
                    project, dry_run=self.dry_run)
            if import_id and not self.dry_run:
                # Disable Shared CI
                self.disable_shared_ci(dst_path_with_namespace, import_id)
                # Post import features
                self.log.info(
                    "Migrating source project {0} (ID: {1}) info".format(path, src_id))
                result[dst_path_with_namespace] = self.migrate_single_project_features(
                    project, import_id)
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

    def disable_shared_ci(self, path, pid):
        # Disable Auto DevOps
        self.log.info(
            f"Disabling Auto DevOps on imported project {path} (ID: {pid})")
        data = {"auto_devops_enabled": False}
        # Disable shared runners
        if not self.config.shared_runners_enabled:
            data["shared_runners_enabled"] = self.config.shared_runners_enabled
        self.projects_api.edit_project(
            self.config.destination_host, self.config.destination_token, pid, data)

    def migrate_single_project_features(self, project, dst_id):
        """
            Subsequent function to update project info AFTER import
        """
        project.pop("members")
        path_with_namespace = project["path_with_namespace"]
        shared_with_groups = project["shared_with_groups"]
        src_id = project["id"]
        jobs_enabled = project["jobs_enabled"]
        results = {}

        results["id"] = dst_id

        # Set default branch
        self.branches.set_branch(
            path_with_namespace, dst_id, project.get("default_branch"))

        # Shared with groups
        results["shared_with_groups"] = self.projects.add_shared_groups(
            dst_id, path_with_namespace, shared_with_groups)

        # Environments
        results["environments"] = self.environments.migrate_project_environments(
            src_id, dst_id, path_with_namespace, jobs_enabled)

        # CI/CD Variables
        results["cicd_variables"] = self.variables.migrate_cicd_variables(
            src_id, dst_id, path_with_namespace, "projects", jobs_enabled)

        # Pipeline Schedule Variables
        results["pipeline_schedule_variables"] = self.variables.migrate_pipeline_schedule_variables(
            src_id, dst_id, path_with_namespace, jobs_enabled)

        # Deploy Keys
        results["deploy_keys"] = self.keys.migrate_project_deploy_keys(
            src_id, dst_id, path_with_namespace)

        # Container Registries
        if self.config.source_registry and self.config.destination_registry:
            results["container_registry"] = self.registries.migrate_registries(
                src_id, dst_id, path_with_namespace)

        # Package Registries
        results["package_registry"] = self.packages.migrate_project_packages(
            src_id, dst_id, path_with_namespace)

        # Hooks (Webhooks)
        results["project_hooks"] = self.hooks.migrate_project_hooks(
            src_id, dst_id, path_with_namespace)

        # Clusters
        results["clusters"] = self.clusters.migrate_project_clusters(
            src_id, dst_id, path_with_namespace, jobs_enabled)

        if self.config.source_tier not in ["core", "free"]:
            # Push Rules - handled by GitLab Importer as of 13.6
            # results["push_rules"] = self.pushrules.migrate_push_rules(
            #     src_id, dst_id, path_with_namespace)

            # Merge Request Approvals
            results["project_level_mr_approvals"] = self.mr_approvals.migrate_project_level_mr_approvals(
                src_id, dst_id, path_with_namespace)

        if self.config.remapping_file_path:
            self.projects.migrate_gitlab_variable_replace_ci_yml(dst_id)

        self.remove_import_user(dst_id)

        return results

    def migrate_jenkins_variables(
            self, project, new_id, jenkins_client, jenkins_ci_src_hostname):
        if (ci_sources := project.get("ci_sources", None)):
            result = True
            for job in ci_sources.get("Jenkins", []):
                params = jenkins_client.jenkins_api.get_job_params(job)
                for param in params:
                    if not self.variables.safe_add_variables(
                        new_id,
                        jenkins_client.transform_ci_variables(
                            param, jenkins_ci_src_hostname)
                    ):
                        result = False
            return result
        return None

    def migrate_jenkins_config_xml(self, project, project_id, jenkins_client):
        '''
        In order to maintain configuration from old Jenkins instance,
        we save a copy of a Jenkins job config.xml file and commit it to the associated repository.
        '''
        if (ci_sources := project.get("ci_sources", None)):
            is_result = False
            for job in ci_sources.get("Jenkins", []):
                if config_xml := jenkins_client.jenkins_api.get_job_config_xml(
                        job):
                    # Create branch for config.xml
                    branch_data = {
                        "branch": "%s-jenkins-config" % job.lstrip("/"),
                        "ref": "master"
                    }
                    self.projects_api.create_branch(
                        self.config.destination_host,
                        self.config.destination_token,
                        project_id,
                        data=branch_data
                    )
                    content = config_xml.text
                    data = {
                        "branch": "%s-jenkins-config" % job.lstrip("/"),
                        "commit_message": "Adding config.xml for Jenkins job",
                        "content": content
                    }

                    req = self.project_repository_api.create_repo_file(
                        self.config.destination_host, self.config.destination_token,
                        project_id, "config.xml", data)
                    is_result = bool(req.status_code == 200)
            return is_result
        return None

    def migrate_teamcity_variables(
            self, project, new_id, tc_client, tc_ci_src_hostname):
        if (ci_sources := project.get("ci_sources", None)):
            result = True
            for job in ci_sources.get("TeamCity", []):
                params = tc_client.teamcity_api.get_build_params(job)
                try:
                    if params.get("properties", None) is not None:
                        for param in dict_utils.dig(
                                params, "properties", "property", default=[]):
                            if not self.variables.safe_add_variables(
                                new_id,
                                tc_client.transform_ci_variables(
                                    param, tc_ci_src_hostname)
                            ):
                                result = False
                    else:
                        self.log.warning(
                            f"Job: {job} had no param properties present")
                except AttributeError as e:
                    self.log.error(
                        f"Attribute Error Caught for Job:{job} Params:{params} with error:{e}")
            return result
        return None

    def migrate_teamcity_build_config(self, project, project_id, tc_client):
        '''
        In order to maintain configuration from old TeamCity instance,
        we save a copy of a TeamCity's job build configuration file and commit it to the associated repoistory.
        '''
        is_result = True
        if ci_sources := project.get("ci_sources", None):
            for job in ci_sources.get("TeamCity", []):
                if build_config := tc_client.teamcity_api.get_build_config(
                        job):
                    # Create branch for TeamCity configuration
                    branch_data = {
                        "branch": "%s-teamcity-config" % job,
                        "ref": "master"
                    }
                    self.projects_api.create_branch(
                        self.config.destination_host,
                        self.config.destination_token,
                        project_id,
                        data=branch_data
                    )

                    dom = xml.dom.minidom.parseString(build_config.text)
                    build_config = dom.toprettyxml()

                    data = {
                        "branch": "%s-teamcity-config" % job,
                        "commit_message": "Adding build_config.xml for TeamCity job",
                        "content": build_config
                    }

                    req = self.project_repository_api.create_repo_file(
                        self.config.destination_host, self.config.destination_token,
                        project_id, "build_config.xml", data)

                    if req.status_code != 200:
                        is_result = False

                    for url in tc_client.teamcity_api.get_maven_settings_file_links(
                            job):
                        file_name, content = tc_client.teamcity_api.extract_maven_xml(
                            url)
                        if content:
                            data = {
                                "branch": "%s-teamcity-config" % job,
                                "commit_message": f"Adding {file_name} for TeamCity job",
                                "content": content
                            }
                            req = self.project_repository_api.create_repo_file(
                                self.config.destination_host, self.config.destination_token,
                                project_id, file_name, data)

                            if req.status_code != 200:
                                is_result = False

        return is_result

    def rollback(self):
        rotate_logs()
        dry_log = misc_utils.get_dry_log(self.dry_run)

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

        mig_utils.add_post_migration_stats(self.start, log=self.log)

    def get_total_migrated_count(self):
        # group_projects = api.get_count(
        # self.config.destination_host, self.config.destination_token,
        # "groups/%d/projects" % self.config.dstn_parent_id)
        subgroup_count = 0
        for group in self.groups_api.get_all_subgroups(self.config.dstn_parent_id,
                                                       self.config.destination_host, self.config.destination_token):
            count = self.groups_api.api.get_count(
                self.config.destination_host, self.config.destination_token, "groups/%d/projects" % group["id"])
            sub_count = 0
            if group.get("child_ids", None) is not None:
                for child_id in group["child_ids"]:
                    sub_count += self.projects_api.api.get_count(self.config.destination_host,
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

    def toggle_maintenance_mode(
            self, off=False, msg=None, dest=False, dry_run=True):
        host = self.config.destination_host if dest else self.config.source_host
        if is_dot_com(host):
            self.log.warning(
                f"Not allowed to toggle maintenance mode on {host}")
        else:
            data = {
                "maintenance_mode": not off}
            if not off and msg:
                data["maintenance_mode_message"] = msg.replace("+", " ")
            token = self.config.destination_token if dest else self.config.source_token
            self.log.warning(
                f"{misc_utils.get_dry_log(dry_run)}Turning maintenance mode {'OFF' if off else 'ON'} on {host}")
            if not dry_run:
                self.instance_api.change_application_settings(
                    host, token, data)

    def remove_import_user(self, dst_id, gl_type="project"):
        import_uid = self.config.import_user_id
        host = self.config.destination_host
        token = self.config.destination_token
        self.log.info(
            f"Removing import user (ID: {import_uid}) from {gl_type} (ID: {dst_id})")
        try:
            if gl_type == "group":
                resp = self.groups_api.remove_member(
                    dst_id, import_uid, host, token)
            else:
                resp = self.projects_api.remove_member(
                    dst_id, import_uid, host, token)
            if not resp or resp.status_code != 204:
                self.log.error(
                    f"Failed to remove import user (ID: {import_uid}) from {gl_type} (ID: {dst_id}):\n{resp}")
        except RequestException as re:
            self.log.error(
                f"Failed to remove import user (ID: {import_uid}) from {gl_type} (ID: {dst_id}), with error:\n{re}")
