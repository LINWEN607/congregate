"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2024 - GitLab
"""

from json import loads as json_loads
from traceback import print_exc
from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import safe_json_response, get_dry_log
from gitlab_ps_utils.json_utils import json_pretty
from gitlab_ps_utils import misc_utils

import congregate.helpers.migrate_utils as mig_utils

from congregate.migration.meta.base_migrate import MigrateClient
from congregate.migration.gitlab.external_import import ImportClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.migration.ado.projects import ProjectsClient
from congregate.migration.ado.export import AdoExportBuilder
from congregate.helpers.migrate_utils import get_export_filename_from_namespace_and_name
from congregate.migration.gitlab.importexport import ImportExportClient

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
        self.migrate_project_info()

        # Migrate Azure repositories as GL projects
        # self.handle_exporting_azure_project(dry_log)
        # self.handle_importing_azure_project(dry_log)

    def migrate_project_info(self):
        staged_projects = mig_utils.get_staged_projects()
        dry_log = get_dry_log(self.dry_run)
        if staged_projects:
            mig_utils.validate_groups_and_projects(
                staged_projects, are_projects=True)
            if user_projects := mig_utils.get_staged_user_projects(
                    staged_projects):
                self.log.warning(
                    f"USER projects staged ({len(user_projects)}):\n{json_pretty(user_projects)}")
            if not self.skip_project_export:
                self.log.info(f"{dry_log}Exporting projects")
                export_results = list(er for er in self.multi.start_multi_process(
                    self.handle_exporting_azure_project, staged_projects, processes=self.processes))

                self.are_results(export_results, "project", "export")

                # Create list of projects that failed export
                if failed := mig_utils.get_failed_export_from_results(
                        export_results):
                    self.log.warning("SKIP: Projects that failed to export or already exist on destination:\n{}".format(
                        json_pretty(failed)))

                # Append total count of projects exported
                export_results.append(mig_utils.get_results(export_results))
                self.log.info("### {0}Project export results ###\n{1}"
                              .format(dry_log, json_pretty(export_results)))

                # Filter out the failed ones
                staged_projects = mig_utils.get_staged_projects_without_failed_export(
                    staged_projects, failed)
            else:
                self.log.info(
                    "SKIP: Assuming staged projects are already exported")

            if not self.skip_project_import:
                self.log.info("{}Importing projects".format(dry_log))
                import_results = list(ir for ir in self.multi.start_multi_process(
                    self.handle_importing_azure_project, staged_projects, processes=self.processes))

                self.are_results(import_results, "project", "import")

                # append Total : Successful count of project imports
                import_results.append(mig_utils.get_results(import_results))
                self.log.info("### {0}Project import results ###\n{1}"
                              .format(dry_log, json_pretty(import_results)))
                mig_utils.write_results_to_file(import_results, log=self.log)
            else:
                self.log.info(
                    "SKIP: Assuming staged projects will be later imported")
        else:
            self.log.warning("SKIP: No projects staged for migration")

    def handle_exporting_azure_project(self, project):
        if self.dry_run:
            exported_file = get_export_filename_from_namespace_and_name(project['path'], project['name'])
            self.log.info(f"DRY-RUN: Would export Azure repo info to {exported_file}")
        else:
            exported_file = AdoExportBuilder(project).create()
            self.log.info(f"Exported Azure repo info to {exported_file}")
        return {
            exported_file: True
        }

    def handle_importing_azure_project(self, project, group_path=None, filename=None):
        src_id = project["id"]
        path = project["path_with_namespace"]
        dst_host = self.config.destination_host
        dst_token = self.config.destination_token
        src_host = self.config.source_host
        src_token = self.config.source_token
        dst_pwn, tn = mig_utils.get_stage_wave_paths(
            project, group_path=group_path)
        result = {
            dst_pwn: False
        }
        import_id = None
        try:
            if self.groups.find_group_id_by_path(dst_host, dst_token, tn):
                if isinstance(project, str):
                    project = json_loads(project)
                dst_pid = self.projects.find_project_by_path(
                    dst_host, dst_token, dst_pwn)

                if dst_pid:
                    import_status = safe_json_response(self.projects_api.get_project_import_status(
                        dst_host, dst_token, dst_pid))
                    self.log.info(
                        f"Project {dst_pwn} (ID: {dst_pid}) found on destination, with import status: {import_status}")
                    if self.only_post_migration_info and not self.dry_run:
                        import_id = dst_pid
                    else:
                        result[dst_pwn] = dst_pid
                else:
                    self.log.info(
                        f"{get_dry_log(self.dry_run)}Project '{dst_pwn}' NOT found on destination, importing...")
                    ie_client = ImportExportClient(
                        dest_host=dst_host, dest_token=dst_token)
                    import_id = ie_client.import_project(
                        project, dry_run=self.dry_run, group_path=group_path or tn)
                if import_id and not self.dry_run:
                    # Disable Shared CI
                    self.disable_shared_ci(dst_pwn, import_id)
                    # Post import features
                    self.log.info(
                        f"Migrating additional source project '{path}' (ID: {src_id}) GitLab features")
                    result[dst_pwn] = self.migrate_single_project_features(
                        project, import_id, dest_host=dst_host, dest_token=dst_token)
            elif not self.dry_run:
                self.log.warning(
                    f"Skipping import. Target namespace {tn} does not exist for project '{path}'")
        except (RequestException, KeyError, OverflowError) as oe:
            self.log.error(
                f"Failed to import project '{path}' (ID: {src_id}):\n{oe}")
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())
        return result
    
    def migrate_single_project_features(project, import_id, dest_host, dest_token):
        pass
    
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
                    f"USER repos staged ({len(user_projects)}):\n{json_pretty(user_projects)}")
            self.log.info("Importing Azure Devops repos")
            import_results = list(ir for ir in self.multi.start_multi_process(
                self.import_azure_repo, staged_projects, processes=self.processes, nestable=True))

            self.are_results(import_results, "project", "import")

            # append Total : Successful count of project imports
            import_results.append(mig_utils.get_results(import_results))
            self.log.info(
                f"### {dry_log}Azure Devops repos import result ###\n{json_pretty(import_results)}")
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
