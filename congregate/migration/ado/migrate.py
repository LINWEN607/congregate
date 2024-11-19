"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2023 - GitLab
"""

from gitlab_ps_utils import json_utils, misc_utils

import congregate.helpers.migrate_utils as mig_utils

from congregate.migration.meta.base_migrate import MigrateClient
from congregate.migration.gitlab.external_import import ImportClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.migration.ado.projects import ProjectsClient




class AzureDevopsMigrateClient(MigrateClient):
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
        self.azure_projects_client = ProjectsClient()
        self.branches = BranchesClient()
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
        
    def migrate(self):
        dry_log = misc_utils.get_dry_log(self.dry_run)

        # Migrate users
        self.migrate_user_info()

        # Migrate Azure projects as GL groups
        # self.migrate_azure_project_info(dry_log)

        # Migrate Azure repositories as GL projects
        self.migrate_azure_repo_info(dry_log)
    
    # def migrate_azure_project_info(self, dry_log):
    #     staged_groups = mig_utils.get_staged_groups()
    #     if staged_groups and not self.skip_group_import and not self.group_structure and not self.config.wave_spreadsheet_path:
    #         mig_utils.validate_groups_and_projects(staged_groups)
    #         self.log.info(
    #             f"{dry_log}Migrating Azure Devops projects as GitLab groups")
    #         results = list(r for r in self.multi.start_multi_process(
    #             self.migrate_external_group, staged_groups, processes=self.processes, nestable=True))

    #         self.are_results(results, "group", "import")

    #         results.append(mig_utils.get_results(results))
    #         self.log.info(
    #             f"### {dry_log}Azure Devops projects migration result ###\n{json_utils.json_pretty(results)}")
    #         mig_utils.write_results_to_file(
    #             results, result_type="group", log=self.log)
    #     # Allow Azure Devops Server importer to create missing sub-group layers on repo import
    #     elif self.group_structure:
    #         self.log.info(
    #             "Skipping Azure Devops projects migration and relying on Azure Devops Server importer to create missing GitLab sub-group layers")
    #     elif self.config.wave_spreadsheet_path:
    #         self.log.warning(
    #             "Skipping Azure Devops projects migration. Not supported when 'wave_spreadsheet_path' is configured")
    #     else:
    #         self.log.warning(
    #             "SKIP: No Azure Devops projects staged for migration")

        
    def migrate_azure_repo_info(self, dry_log):
        staged_projects = mig_utils.get_staged_projects()
        if staged_projects and not self.skip_project_import:
            mig_utils.validate_groups_and_projects(
                staged_projects, are_projects=True)
            if user_projects := mig_utils.get_staged_user_projects(
                    staged_projects):
                self.log.warning(
                    f"USER repos staged ({len(user_projects)}):\n{json_utils.json_pretty(user_projects)}")
            self.log.info("Importing Azure Devops repos")
            import_results = list(ir for ir in self.multi.start_multi_process(
                self.import_azure_repo, staged_projects, processes=self.processes, nestable=True))

            self.are_results(import_results, "project", "import")

            # append Total : Successful count of project imports
            import_results.append(mig_utils.get_results(import_results))
            self.log.info(
                f"### {dry_log}Azure Devops repos import result ###\n{json_utils.json_pretty(import_results)}")
            mig_utils.write_results_to_file(import_results, log=self.log)
        else:
            self.log.warning(
                "SKIP: No Azure Devops repos staged for migration")

    def import_azure_repo(self, project):
        if project.get("namespace"):
            pn = self.config.dstn_parent_group_path+"/"+project.get("namespace")
        else:
            pn = self.config.dstn_parent_group_path
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
                    result = self.handle_azure_post_migration(
                        result, dstn_pwn, project, dst_pid)
                else:
                    self.log.warning(
                        f"Skipping import. Repo {dstn_pwn} has already been imported")
            # New import
            else:
                result = self.ext_import.trigger_import_from_repo(
                    pn, dstn_pwn, tn, project, dry_run=self.dry_run)
                result_response = result[dstn_pwn]["response"]
                if (isinstance(result_response, dict)) and (project_id := result_response.get("id")):
                    full_path = result_response.get("path_with_namespace").strip("/")
                    success = self.ext_import.wait_for_project_to_import(
                        full_path)
                    if success:
                        result = self.handle_azure_post_migration(
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

    def handle_azure_post_migration(self, result, path_with_namespace, project, pid):

        # Set default branch
        self.branches.set_branch(
            path_with_namespace, pid, project.get("default_branch"))

        # Pull Requests migration
        self.azure_projects_client.migrate_pull_requests(project, pid)

        # Remove import user; SKIP if removing all other members
        # if not self.remove_members:
        #     self.remove_import_user(pid)
        return result
