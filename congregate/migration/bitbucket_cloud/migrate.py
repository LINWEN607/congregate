"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2023 - GitLab
"""

from gitlab_ps_utils import json_utils, misc_utils

import congregate.helpers.migrate_utils as mig_utils

from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.meta.base_migrate import MigrateClient
from congregate.migration.gitlab.external_import import ImportClient
from congregate.migration.bitbucket_cloud.base import BitBucketCloud
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi


class BitbucketCloudMigrateClient(MigrateClient):
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
        self.gl_projects_api = ProjectsApi()
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
        self.bb_cloud = BitBucketCloud()

    def migrate(self):
        dry_log = misc_utils.get_dry_log(self.dry_run)

        # Migrate users
        self.migrate_user_info()

        # Migrate BB workspaces as groups
        self.migrate_bitbucket_cloud_workspace_info(dry_log)

        # Migrate BB repos as projects
        self.migrate_bitbucket_cloud_repo_info(dry_log)

    def migrate_bitbucket_cloud_workspace_info(self, dry_log):
        staged_groups = mig_utils.get_staged_groups()
        if staged_groups and not self.skip_group_import and not self.group_structure and not self.config.wave_spreadsheet_path:
            mig_utils.validate_groups_and_projects(staged_groups)

            # Add empty members list to each group if missing
            for group in staged_groups:
                if "members" not in group:
                    group["members"] = []

            self.log.info(
                f"{dry_log}Migrating Bitbucket Cloud workspaces as GitLab groups")
            results = list(r for r in self.multi.start_multi_process(
                self.migrate_external_group, staged_groups, processes=self.processes, nestable=True))
            self.are_results(results, "group", "import")
            results.append(mig_utils.get_results(results))
            self.log.info(
                f"### {dry_log}Bitbucket Cloud workspaces migration result ###\n{json_utils.json_pretty(results)}")
            mig_utils.write_results_to_file(
                results, result_type="group", log=self.log)
        elif self.group_structure:
            self.log.info(
                "Skipping Bitbucket Cloud workspaces migration and relying on Bitbucket Cloud importer to create missing GitLab group layers")
        elif self.config.wave_spreadsheet_path:
            self.log.warning(
                "Skipping Bitbucket Cloud workspaces migration. Not supported when 'wave_spreadsheet_path' is configured")
        else:
            self.log.warning("SKIP: No Bitbucket Cloud workspaces staged for migration")

    def migrate_bitbucket_cloud_repo_info(self, dry_log):
        import_results = None
        staged_projects = mig_utils.get_staged_projects()
        if staged_projects and not self.skip_project_import:
            mig_utils.validate_groups_and_projects(
                staged_projects, are_projects=True)
            if user_projects := mig_utils.get_staged_user_projects(
                    staged_projects):
                self.log.warning(
                    f"USER repos staged (Count : {len(user_projects)}):\n{json_utils.json_pretty(user_projects)}")
            self.log.info("Importing repos from Bitbucket Cloud")
            import_results = list(ir for ir in self.multi.start_multi_process(
                self.import_bitbucket_cloud_repo, staged_projects, processes=self.processes, nestable=True))

            self.are_results(import_results, "project", "import")
            # append Total : Successful count of project imports
            import_results.append(mig_utils.get_results(import_results))
            self.log.info(
                f"### {dry_log}Bitbucket Cloud repos import result ###\n{json_utils.json_pretty(import_results)}")
            mig_utils.write_results_to_file(import_results, log=self.log)
        else:
            self.log.warning("SKIP: No Bitbucket Cloud repos staged for migration")

        # After all is said and done, run our reporting with the
        # staged_projects and results
        if staged_projects and import_results:
            self.create_issue_reporting(staged_projects, import_results)

    def import_bitbucket_cloud_repo(self, project):
        """
        Import a Bitbucket Cloud repository to GitLab using GitLab's built-in importer

        :param project: Project data from staged_projects
        :return: Import result
        """
        bb_username = self.config.source_username
        bb_token = self.config.source_token

        dstn_pwn, tn = mig_utils.get_stage_wave_paths(project)
        host = self.config.destination_host
        token = self.config.destination_token
        project_id = None

        # Parse the path_with_namespace to get the workspace and repo slug
        if '/' in project['path_with_namespace']:
            workspace, repo_slug = project['path_with_namespace'].split('/', 1)
        else:
            self.log.error(f"Invalid path_with_namespace: {project['path_with_namespace']}")
            return self.ext_import.get_failed_result(
                dstn_pwn,
                data={"error": f"Invalid path_with_namespace: {project['path_with_namespace']}"})

        # Use the configured workspace instead of the parsed one
        workspace = self.config.src_parent_workspace

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
                result = self.ext_import.trigger_import_from_bitbucket_cloud(
                    project, workspace, repo_slug, dstn_pwn, tn, bb_username, bb_token, dry_run=self.dry_run)
                result_response = result[dstn_pwn]["response"]
                if (isinstance(result_response, dict)) and (project_id := result_response.get("id")):
                    full_path = result_response.get("full_path", "").strip("/")
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
                        data={"error": f"Failed import, with response/payload {result_response}. Unable to execute post migration phase"})

            # Repo import status
            if dst_pid or project_id:
                result[dstn_pwn]["import_status"] = self.ext_import.get_external_repo_import_status(
                    host, token, dstn_pwn, dst_pid or project_id)
        else:
            log = f"Target namespace {tn} does not exist"
            self.log.warning("Skipping import. " + log + f" for {project['path']}")
            result = self.ext_import.get_result_data(dstn_pwn, {
                "error": log
            })

        return result

    def handle_bb_post_migration(self, result, path_with_namespace, project, pid):
        """
        Handle post-migration tasks for a Bitbucket Cloud repository

        :param result: Current result
        :param path_with_namespace: Path with namespace
        :param project: Project data
        :param pid: Project ID
        :return: Updated result
        """
        # Extract members info
        members = project.pop("members", [])

        # Add members to destination project
        result[path_with_namespace]["members"] = self.projects.add_members_to_destination_project(
            self.config.destination_host, self.config.destination_token, pid, members)

        # Disable Shared CI
        self.disable_shared_ci(path_with_namespace, pid)

        # Migrate any external CI data
        self.handle_ext_ci_src_migration(result, project, pid)

        # Archive migrated repos on destination if the source was archived
        if project.get("isArchived"):
            result[path_with_namespace]["archived"] = self.archive_migrated_repo(pid, project)
        else:
            result[path_with_namespace]["archived"] = False

        # Determine whether to remove all repo members
        result[path_with_namespace]["members"]["email"] = self.handle_member_retention(
            members, pid)

        # Remove import user; SKIP if removing all other members
        if not self.remove_members:
            self.remove_import_user(pid)

        return result

    def archive_migrated_repo(self, pid, project):
        """
        Archive a migrated repository on GitLab

        :param pid: Project ID on GitLab
        :param project: Project data from Bitbucket Cloud
        :return: Success status
        """
        if project.get("isArchived"):
            response = self.gl_projects_api.archive_project(
                self.config.destination_host,
                self.config.destination_token,
                pid
            )
            return response.status_code == 200
        return False