from traceback import print_exc
from requests.exceptions import RequestException
from json import loads as json_loads
from gitlab_ps_utils import json_utils, misc_utils
from gitlab_ps_utils.json_utils import json_pretty

import congregate.helpers.migrate_utils as mig_utils

from congregate.migration.meta.base_migrate import MigrateClient
from congregate.migration.gitlab.external_import import ImportClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.migration.gitlab.importexport import ImportExportClient
from congregate.migration.codecommit.projects import ProjectsClient
from congregate.migration.codecommit.export import CodeCommitExportBuilder
from congregate.helpers.migrate_utils import get_export_filename_from_namespace_and_name

import requests



class CodeCommitMigrateClient(MigrateClient):
    def __init__(self,
                 dry_run=True,
                 processes=None,
                 only_post_migration_info=False,
                 start=None,
                 skip_users=True,
                 remove_members=False,
                 hard_delete=False,
                 stream_groups=True,
                 skip_groups=True,
                 skip_projects=False,
                 skip_group_export=True,
                 skip_group_import=True,
                 skip_project_export=False,
                 skip_project_import=False,
                 subgroups_only=False,
                 scm_source=None,
                 group_structure=False):
        self.ext_import = ImportClient()
        self.project_repository_api = ProjectRepositoryApi()
        self.codecommit_projects_client = ProjectsClient()
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
        # self.migrate_user_info()

        # Migrate CodeCodemmit repositories as GL projects
        self.migrate_codecommit_repo_info(dry_log)
     
    def migrate_codecommit_repo_info(self, dry_log):
        staged_projects = mig_utils.get_staged_projects()
        if staged_projects:
            mig_utils.validate_groups_and_projects(
                staged_projects, are_projects=True)
            if user_projects := mig_utils.get_staged_user_projects(
                    staged_projects):
                self.log.warning(
                    f"USER repos staged ({len(user_projects)}):\n{json_utils.json_pretty(user_projects)}")
            # if not self.skip_project_import:
            #     self.log.info("Importing CodeCommit repos")
            #     import_results = []
            #     for p in staged_projects:
            #         result = self.import_codecommit_repo(p, p.get("name"))
            #         import_results.append(result)
            #     #TODO: implement multi-processor with multiple function arguments
            #     # import_results = list(ir for ir in self.multi.start_multi_process(
            #     #     self.import_codecommit_repo, staged_projects, processes=self.processes, nestable=False))
            #     self.are_results(import_results, "project", "import")
            #     # append Total : Successful count of project imports
            #     import_results.append(mig_utils.get_results(import_results))
            #     self.log.info(
            #         f"### {dry_log}CodeCommit repos import result ###\n{json_utils.json_pretty(import_results)}")
            #     mig_utils.write_results_to_file(import_results, log=self.log)
            # else:
            #     self.log.warning(
            #         "SKIP: No CodeCommit repos staged for migration")
            # TODO: Implement project export
            if not self.skip_project_export:
                self.log.info(f"{dry_log}Exporting projects")
                export_results = [self.handle_exporting_codecommit_project(prj) for prj in staged_projects]

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
                self.log.info(f"{dry_log}Importing projects")
                import_results = []
                for p in staged_projects:
                    result = self.handle_importing_codecommit_project(p, p.get("path"))
                    import_results.append(result)
                self.are_results(import_results, "project", "import")
            

    def verify_token_permissions(self, host, token):
        try:
            test_response = self.groups_api.get_groups(host, token)
            self.log.info(f"Token permissions test response: {test_response.status_code}")
            if test_response.status_code == 403:
                self.log.error(f"Token validation failed. Response: {test_response.text}")
            return test_response.status_code == 200
        except Exception as e:
            self.log.error(f"Token validation error: {str(e)}")
            return False

    def import_codecommit_repo(self, project, repo_name):
        dstn_pwn, tn = mig_utils.get_stage_wave_paths(project)
        host = self.config.destination_host
        token = self.config.destination_token
        project_id = None
        target_namespace = tn

        if not self.groups.find_group_id_by_path(host, token, target_namespace):
            self.log.info(f"Creating target namespace: {target_namespace}")
            
            # Add more detailed error logging
            result = self.groups_api.create_group(
                host, 
                token,
                {
                    "name": target_namespace,
                    "path": target_namespace,
                    "visibility": "private"  
                }
            )
            
            if isinstance(result, requests.Response) and result.status_code == 403:
                self.log.error(f"Group creation failed. Response: {result.text}")
                return self.ext_import.get_failed_result(
                    dstn_pwn,
                    data={"error": f"Failed to create namespace {target_namespace}. Status: {result.status_code}, Details: {result.text}"}
                )

        if self.group_structure or self.groups.find_group_id_by_path(host, token, target_namespace):
            # Already imported
            print("Already imported")
            if dst_pid := self.projects.find_project_by_path(host, token, dstn_pwn):
                result = self.ext_import.get_result_data(
                    dstn_pwn, {"id": dst_pid})
                if self.only_post_migration_info:
                    result = self.handle_codecommit_post_migration(
                        result, dstn_pwn, project, dst_pid)
                else:
                    self.log.warning(
                        f"Skipping import. Repo {dstn_pwn} has already been imported")
            # New import
            else:
                self.log.info(f"New Import")
                result = self.ext_import.trigger_import_from_codecommit(
                    repo_name, dstn_pwn, target_namespace, dry_run=self.dry_run)
                result_response = result[dstn_pwn]["response"]
                if (isinstance(result_response, dict)) and (project_id := result_response.get("id")):
                    full_path_result = result_response.get("name_with_namespace").strip("/")
                    full_path = "".join(full_path_result.split())
                    success = self.ext_import.wait_for_project_to_import(
                        full_path)
                    if success:
                        result = self.handle_codecommit_post_migration(
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
            log = f"Target namespace {target_namespace} does not exist"
            self.log.warning("Skipping import. " + log +
                             f" for {project['path']}")
            result = self.ext_import.get_result_data(dstn_pwn, {
                "error": log
            })
        return result

    def handle_codecommit_post_migration(self, result, path_with_namespace, project, pid):

        # Set default branch
        self.branches.set_branch(
            path_with_namespace, pid, project.get("default_branch"))
        
        # Pull Requests migration
        self.codecommit_projects_client.migrate_pull_requests(project, pid)

        # Remove import user; SKIP if removing all other members
        if not self.remove_members:
            self.remove_import_user(pid)
        return result

    def handle_exporting_codecommit_project(self, project):
        if not self.dry_run:
            exported_file = CodeCommitExportBuilder(project).create()
        else:
            exported_file = get_export_filename_from_namespace_and_name(project['path'], project['name'])
        self.log.info(f"DRY-RUN: Exported CodeCommit repo info to {exported_file}")
        return {
            exported_file: True
        }
    
    def handle_importing_codecommit_project(self, project, group_path=None, filename=None):
        src_id = project["id"]
        path = project["path_with_namespace"]
        dst_host = self.config.destination_host
        dst_token = self.config.destination_token
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
                    import_status = misc_utils.safe_json_response(self.projects_api.get_project_import_status(
                        dst_host, dst_token, dst_pid))
                    self.log.info(
                        f"Project {dst_pwn} (ID: {dst_pid}) found on destination, with import status: {import_status}")
                    if self.only_post_migration_info and not self.dry_run:
                        import_id = dst_pid
                    else:
                        result[dst_pwn] = dst_pid
                else:
                    self.log.info(
                        f"{mig_utils.get_dry_log(self.dry_run)}Project '{dst_pwn}' NOT found on destination, importing...")
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
                    # Process attachments in MRs after project import
                    # self.process_attachments_after_import(import_id)
                    result[dst_pwn] = import_id
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
