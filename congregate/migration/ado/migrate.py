"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2024 - GitLab
"""

import re
from json import loads as json_loads
from traceback import print_exc
from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import safe_json_response, get_dry_log
from gitlab_ps_utils.json_utils import json_pretty
from gitlab_ps_utils import misc_utils
from congregate.migration.meta import constants

import congregate.helpers.migrate_utils as mig_utils

from congregate.migration.meta.base_migrate import MigrateClient
from congregate.migration.gitlab.external_import import ImportClient
from congregate.migration.gitlab.importexport import ImportExportClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.migration.ado.api.pull_requests import PullRequestsApi
from congregate.migration.gitlab.api.projects import ProjectsApi as GitlabProjectsApi
from congregate.migration.ado.api.projects import ProjectsApi as AdoProjectsApi
from congregate.migration.ado.projects import ProjectsClient
from congregate.migration.ado.export import AdoExportBuilder
from congregate.migration.ado.export import AdoGroupExportBuilder
from congregate.helpers.migrate_utils import get_export_filename_from_namespace_and_name
from congregate.migration.gitlab.importexport import ImportExportClient
from congregate.migration.gitlab.variables import VariablesClient

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
        self.ie = ImportExportClient()
        self.project_repository_api = ProjectRepositoryApi()
        self.merge_requests_api = MergeRequestsApi()
        self.pull_requests_api = PullRequestsApi()
        self.gitlab_projects_api = GitlabProjectsApi()
        self.gitlab_variables_api = VariablesClient()
        self.ado_projects_api = AdoProjectsApi()
        self.azure_projects_client = ProjectsClient()
        self.branches = BranchesClient()
        super().__init__(dry_run,
                         processes,
                         only_post_migration_info,
                         start,
                         skip_users,
                         remove_members,
                         False,
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

        self.migrate_group_info()

        # Migrate Azure projects as GL groups
        self.migrate_project_info()

    def migrate_group_info(self):
        staged_groups = mig_utils.get_staged_groups()
        dry_log = get_dry_log(self.dry_run)
        if staged_groups:
            if not self.skip_group_export:
                self.log.info(f"{dry_log}Exporting groups")
                export_results = list(er for er in self.multi.start_multi_process(
                    self.handle_exporting_azure_group, staged_groups, processes=self.processes))
                
                self.are_results(export_results, "group", "export")
                
                # Create list of groups that failed export
                if failed := mig_utils.get_failed_export_from_results(
                        export_results):
                    self.log.warning("SKIP: Groups that failed to export or already exist on destination:\n{}".format(
                        json_pretty(failed)))

                # Append total count of groups exported
                export_results.append(mig_utils.get_results(export_results))
                self.log.info("### {0}Group export results ###\n{1}"
                              .format(dry_log, json_pretty(export_results)))

                # Filter out the failed ones
                staged_groups = mig_utils.get_staged_groups_without_failed_export(
                    staged_groups, failed)
            else:
                self.log.info(
                    "SKIP: Assuming staged groups are already exported")
            if not self.skip_group_import:
                self.log.info("{}Importing groups".format(dry_log))
                import_results = list(ir for ir in self.multi.start_multi_process(
                    self.handle_importing_azure_group, staged_groups, processes=self.processes))
                
                self.are_results(import_results, "group", "import")

                # append Total : Successful count of group imports
                import_results.append(mig_utils.get_results(import_results))
                self.log.info("### {0}Group import results ###\n{1}"
                              .format(dry_log, json_pretty(import_results)))
            else:
                self.log.info(
                    "SKIP: Assuming staged groups will be later imported")
        else:
            self.log.warning("SKIP: No groups staged for migration")

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
            # print(self.skip_project_export)
            # print(self.skip_project_import)


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

    def handle_exporting_azure_group(self, group):
        if self.dry_run:
            exported_file = get_export_filename_from_namespace_and_name(group['full_path'], group['name'])
            self.log.info(f"DRY-RUN: Would export Azure group info to {exported_file}")
        else:
            exported_file = AdoGroupExportBuilder(group).create()
            self.log.info(f"Exported Azure group info to {exported_file}")
        return {
            exported_file: True
        }

    def handle_importing_azure_group(self, group, filename=None):
        try:
            if isinstance(group, str):
                group = json_loads(group)
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
            dry_log = get_dry_log(self.dry_run)
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
                # Disable Shared CI
                # self.disable_shared_ci(full_path_with_parent_namespace, import_id)
                result[full_path_with_parent_namespace] = import_id
        except (RequestException, KeyError, OverflowError) as oe:
            self.log.error(
                f"Failed to import group {full_path} (ID: {src_gid}) as {filename} with error:\n{oe}")
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())
        return result


    def handle_exporting_azure_project(self, project):
        if self.dry_run:
            exported_file = get_export_filename_from_namespace_and_name(project['namespace'], project['name'])
            self.log.info(f"DRY-RUN: Would export Azure project info to {exported_file}")
        else:
            exported_file = AdoExportBuilder(project).create()
            self.log.info(f"Exported Azure project info to {exported_file}")
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
                    # Process attachments in MRs after project import
                    self.process_attachments_after_import(import_id)
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

    def process_attachments_after_import(self, project_id):
        """
        Finds all ADO attachment URLs in merge request notes and replaces them
        with uploaded versions stored in GitLab.
        """
        self.log.info(f"Processing attachments for project {project_id}...")

        response = self.merge_requests_api.get_all_project_merge_requests(project_id, self.config.destination_host, self.config.destination_token)
        merge_requests = safe_json_response(response)

        # Loop through merge requests and their notes
        for mr in merge_requests:
            mr_id = mr["iid"]
            notes_response = self.merge_requests_api.get_merge_request_notes(self.config.destination_host, self.config.destination_token, project_id, mr_id)
            notes = safe_json_response(notes_response)

            # Process each note to replace ADO attachments with GitLab-hosted ones
            for note in notes:
                note_id = note["id"]
                note_body = note["body"]

                # Find all ADO attachment links
                attachment_urls = re.findall(constants.ADO_ATTACHMENT_PATTERN, note_body)

                if not attachment_urls:
                    continue  # No attachment to process

                for markdown_prefix, file_name, ado_url in attachment_urls:
                    is_image = markdown_prefix == "!"  # Identify images correctly
                    # Process attachment and get new GitLab URL
                    new_gitlab_url = self.process_attachment(ado_url.strip(), project_id)

                    if new_gitlab_url:
                        # Preserve correct Markdown formatting
                        new_markdown = f"![]({new_gitlab_url})" if is_image else f"[{file_name}]({new_gitlab_url})"
                        # Replace old ADO URL with new GitLab URL
                        note_body = note_body.replace(f"{markdown_prefix}[{file_name}]({ado_url})", new_markdown)

                # Update the note with new attachment links
                update_response = self.merge_requests_api.update_merge_request_note(self.config.destination_host, self.config.destination_token, project_id, mr_id, note_id, note=note_body)

                if update_response.status_code == 200:
                    self.log.info(f"Updated note {note_id} in MR {mr_id} with GitLab-hosted Attachments.")
                else:
                    self.log.error(f"Failed to update note {note_id} in MR {mr_id}: {update_response.text}")

    def process_attachment(self, ado_url, project_id):
        """
        Downloads the attachment from the ADO URL and uploads it as an attachment.
        Returns the new URL for the attachment.
        """
        try:
            download_response = self.pull_requests_api.download_file_from_ado(ado_url, self.config.source_token)

            if download_response.status_code != 200 and download_response.status_code != 203:
                self.log.error(f"Failed to download attachment from {ado_url}: {download_response.status_code}")
                return None

            attachment_data = download_response.content
            filename = ado_url.split("/")[-1]
            upload_response = self.gitlab_projects_api.upload_attachment(self.config.destination_host, self.config.destination_token, project_id, attachment_data, filename)

            if upload_response.status_code == 201:
                json_response = safe_json_response(upload_response)
                if 'url' in json_response:
                    new_url = f"{json_response['url']}"
                else:
                    self.log.error(f"Upload succeeded but no URL found in response: {json_response}")
            else:
                self.log.error(f"Failed to upload file {filename}. Response: {upload_response.text}")
                new_url = None
            
            return new_url
        except Exception as e:
            self.log.error(f"Error processing attachment from {ado_url}: {e}")
            return None
        
    def migrate_cicd_variables(self, ado_project_name, ado_project_id, group_id):
        """
        Finds all ADO variable groups and variables in the project
        and creates them in the GitLab group.
        """
        self.log.info(f"Migrating ADO variable groups and variables from ADO project {ado_project_name} (ID: {ado_project_id}) to GitLab Group ID: {group_id}...")
        variable_groups = self.ado_projects_api.get_all_variable_groups(ado_project_id).json()
        for group in variable_groups.get("value", []):
            group_name = group.get("name", "Unnamed Group")
            self.log.info(f"Processing variable group: {group_name} (ID: {group.get('id')})")
            variables = group.get("variables", {})
            for key, value_data in variables.items():
                value = value_data.get("value", "")
                self.gitlab_variables_api.set_variables(
                    group_id, self.config.destination_host, self.config.destination_token, var_type="group", data={"key": key, "value": value})