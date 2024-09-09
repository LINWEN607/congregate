"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2023 - GitLab
"""

from gitlab_ps_utils import json_utils, misc_utils, string_utils

import congregate.helpers.migrate_utils as mig_utils
from congregate.helpers.utils import is_dot_com

from congregate.migration.meta.base_migrate import MigrateClient
from congregate.migration.gitlab.external_import import ImportClient
from congregate.migration.github.repos import ReposClient as GHReposClient
from congregate.migration.github.keys import KeysClient as GHKeysClient
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.helpers.jobtemplategenerator import JobTemplateGenerator


class GitHubMigrateClient(MigrateClient):
    def __init__(self,
                 dry_run=True,
                 processes=None,
                 only_post_migration_info=False,
                 start=None,
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
                 group_structure=False):
        self.ext_import = ImportClient()
        self.project_repository_api = ProjectRepositoryApi()
        super().__init__(dry_run,
                         processes,
                         only_post_migration_info,
                         start,
                         skip_users,
                         remove_members,
                         hard_delete,
                         stream_groups,
                         skip_groups,
                         skip_projects,
                         skip_group_export,
                         skip_group_import,
                         skip_project_export,
                         skip_project_import,
                         subgroups_only,
                         scm_source,
                         group_structure)
        self.gh_keys = GHKeysClient()

    def migrate(self):
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
            mig_utils.validate_groups_and_projects(staged_groups)
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
            mig_utils.validate_groups_and_projects(
                staged_projects, are_projects=True)
            if user_projects := mig_utils.get_staged_user_projects(
                    staged_projects):
                self.log.warning(
                    f"USER repos staged (Count : {len(user_projects)}):\n{json_utils.json_pretty(user_projects)}")
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

    def import_github_repo(self, project):
        dstn_pwn, tn = mig_utils.get_stage_wave_paths(project)
        host = self.config.destination_host
        token = self.config.destination_token
        project_id = None
        if self.group_structure or self.groups.find_group_id_by_path(host, token, tn):
            gh_host, gh_token = self.get_host_and_token()
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
        for single_source in self.config.list_multiple_source_config(
                "github_source"):
            if self.scm_source in single_source.get("src_hostname"):
                gh_host = single_source["src_hostname"]
                gh_token = string_utils.deobfuscate(
                    single_source["src_access_token"])
                self.gh_repos = GHReposClient(gh_host, gh_token)
                return gh_host, gh_token
        gh_host = self.config.source_host
        gh_token = self.config.source_token
        self.gh_repos = GHReposClient(gh_host, gh_token)
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

        # Migrate deploy keys
        result[path_with_namespace]["deploy_keys"] = self.gh_keys.migrate_project_deploy_keys(
            pid, project)

        # Remove import user; SKIP if removing all other members
        if not self.remove_members:
            self.remove_import_user(pid)

        return result

    def add_pipeline_for_github_pages(self, project_id):
        '''
        GH pages utilizes a separate branch (gh-pages) for its pages feature.
        We lookup the branch on destination once the project imports and add the .gitlab-ci.yml file
        '''
        jtg = JobTemplateGenerator()
        is_result = False
        data = {
            "branch": "gh-pages",
            "commit_message": "[skip ci] Adding '.gitlab-ci.yml' for publishing GitHub pages",
            "content": jtg.generate_plain_html_template()
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
