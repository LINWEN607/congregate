"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2023 - GitLab
"""

from json import loads as json_loads
from traceback import print_exc
from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import safe_json_response, strip_netloc, get_dry_log
from gitlab_ps_utils.json_utils import write_json_to_file, json_pretty
from celery import shared_task
from dacite import from_dict

import congregate.helpers.migrate_utils as mig_utils
from congregate.helpers.utils import is_dot_com
from congregate.helpers.airgap_utils import create_archive, delete_project_features, extract_archive, delete_project_export

from congregate.migration.meta.base_migrate import MigrateClient
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
from congregate.migration.gitlab.environments import EnvironmentsClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.packages import PackagesClient
from congregate.migration.gitlab.project_feature_flags import ProjectFeatureFlagClient
from congregate.migration.gitlab.pushrules import PushRulesClient
from congregate.migration.gitlab.project_feature_flags_user_lists import ProjectFeatureFlagsUserListsClient
from congregate.helpers.congregate_mdbc import CongregateMongoConnector, mongo_connection
from congregate.migration.meta.api_models.single_project_features import SingleProjectFeatures
from congregate.migration.meta.api_models.project_details import ProjectDetails
from congregate.migration.meta.api_models.bulk_import_entity_status import BulkImportEntityStatus
from congregate.migration.gitlab.contributor_retention import ContributorRetentionClient
from congregate.migration.gitlab.issue_links import IssueLinksClient


class GitLabMigrateClient(MigrateClient):
    def __init__(self,
                 dry_run=True,
                 processes=None,
                 only_post_migration_info=False,
                 start=None,
                 skip_users=False,
                 remove_members=False,
                 sync_members=False,
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
                 group_structure=False,
                 reg_dry_run=False,
                 retain_contributors=False):
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
        self.environments = EnvironmentsClient()
        self.branches = BranchesClient()
        self.pushrules = PushRulesClient()
        self.project_feature_flags_client = ProjectFeatureFlagClient(
            DRY_RUN=False)
        self.issue_links_client = IssueLinksClient(
            DRY_RUN=False)
        self.project_feature_flags_users_lists_client = ProjectFeatureFlagsUserListsClient(
            DRY_RUN=False)
        self.project_id_mapping = {}
        super().__init__(dry_run,
                         processes,
                         only_post_migration_info,
                         start,
                         skip_users,
                         remove_members,
                         sync_members,
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
                         group_structure,
                         retain_contributors)

    def migrate(self):
        # Users
        self.migrate_user_info()

        # Groups
        self.migrate_group_info()

        # Projects
        self.migrate_project_info()

        # Instance hooks
        self.hooks.migrate_instance_hooks(dry_run=self.dry_run)

        # Remove import user from parent group to avoid inheritance
        # (self-managed only)
        if not self.dry_run and self.config.dstn_parent_id and not is_dot_com(
                self.config.destination_host) and not self.skip_project_import:
            self.remove_import_user(
                self.config.dstn_parent_id, gl_type="group")

    def migrate_group_info(self):
        staged_groups = mig_utils.get_staged_groups()
        staged_top_groups = [
            g for g in staged_groups if mig_utils.is_top_level_group(g)]
        staged_subgroups = [
            g for g in staged_groups if not mig_utils.is_top_level_group(g)]
        dry_log = get_dry_log(self.dry_run)
        if staged_top_groups or (staged_subgroups and self.subgroups_only):
            mig_utils.validate_groups_and_projects(staged_groups)
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
                    f"SKIP: Groups that failed to export or already exist on destination:\n{json_pretty(failed)}")

            # Append total count of groups exported
            export_results.append(mig_utils.get_results(export_results))
            self.log.info(
                f"### {dry_log}Group export results ###\n{json_pretty(export_results)}")

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
                f"### {dry_log}Group import results ###\n{json_pretty(import_results)}")
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
            f"### {dry_log}Group bulk import results ###\n{json_pretty(import_results)}")
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
                f"{dry_log}Start bulk group import, with payload:\n{json_pretty(data['entities'])} and destination state:\n{json_pretty(result)}")

            if data["entities"] and not self.dry_run:
                bulk_import_resp = self.groups_api.bulk_group_import(
                    host, token, data=data)
                if bulk_import_resp.status_code != 201:
                    self.log.error(
                        f"Failed to trigger group bulk import, with response:\n{bulk_import_resp} - {bulk_import_resp.text}")
                else:
                    bid = safe_json_response(
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
        dry_log = get_dry_log(self.dry_run)
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
                subgroup = json_loads(subgroup)
            full_path = subgroup["full_path"]
            src_gid = subgroup["id"]
            full_path_with_parent_namespace = mig_utils.get_full_path_with_parent_namespace(
                full_path)
            result = {
                full_path_with_parent_namespace: False
            }
            if self.dry_run:
                dst_gid = self.groups.find_group_id_by_path(
                    self.config.destination_host, self.config.destination_token, full_path_with_parent_namespace)
                dst_grp = {}
            else:
                dst_grp = self.ie.wait_for_group_import(
                    full_path_with_parent_namespace)
                dst_gid = dst_grp.get("id") if dst_grp else None
            if dst_gid:
                self.log.info(f"{get_dry_log(self.dry_run)}Importing sub-group '{full_path_with_parent_namespace}' (ID: {dst_gid}) features... ")
                if not self.dry_run:
                    # Temporarily fixing group import subgroup visibility bug - https://gitlab.com/gitlab-org/gitlab/-/issues/405168
                    if dst_grp.get("visibility") != subgroup["visibility"]:
                        self.groups_api.update_group(
                            dst_gid,
                            self.config.destination_host,
                            self.config.destination_token,
                            data={"visibility": subgroup["visibility"]})
                    result[full_path_with_parent_namespace] = self.migrate_single_group_features(
                        src_gid, dst_gid, full_path)
            elif not self.dry_run:
                self.log.warning(
                    f"SKIP: Sub-group '{full_path_with_parent_namespace}' NOT found on destination")
        except (RequestException, KeyError, OverflowError) as oe:
            self.log.error(
                f"Failed to migrate sub-group {full_path_with_parent_namespace} (ID: {src_gid}) features with error:\n{oe}")
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

        # Add missing members; SKIP if removing all other members
        if self.sync_members and not self.remove_members:
            results["members_added"] = self.add_group_members(
                src_gid, dst_gid, full_path)

        # Add group members to groups
        results["shared_with_groups"] = self.share_groups_with_groups(
            src_gid, dst_gid)

        return results

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
                    self.handle_exporting_projects, staged_projects, processes=self.processes))

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
                    self.handle_importing_projects, staged_projects, processes=self.processes))

                self.are_results(import_results, "project", "import")

                # append Total : Successful count of project imports
                import_results.append(mig_utils.get_results(import_results))
                self.log.info("### {0}Project import results ###\n{1}"
                              .format(dry_log, json_pretty(import_results)))
                mig_utils.write_results_to_file(import_results, log=self.log)
                # Run reporting
                if staged_projects and import_results:
                    self.create_issue_reporting(staged_projects, import_results)
            else:
                self.log.info(
                    "SKIP: Assuming staged projects will be later imported")
        else:
            self.log.warning("SKIP: No projects staged for migration")

    def handle_exporting_projects(self, project, src_host=None, src_token=None):
        pid = project["id"]
        project_path = project['path_with_namespace']
        dry_log = get_dry_log(self.dry_run)
        filename = mig_utils.get_export_filename_from_namespace_and_name(
            project["namespace"], name=project["name"])
        result = {
            filename: False
        }
        try:
            c_retention = None
            if self.retain_contributors and not self.config.direct_transfer:
                self.log.info(
                    f"{dry_log}Contributor Retention is enabled. Adding all project contributors as project members")
                c_retention = ContributorRetentionClient(
                    pid, None, project_path, dry_run=self.dry_run)
                c_retention.build_map()
                c_retention.add_contributors_to_project()
            self.log.info(
                f"{dry_log}Exporting project {project_path} (ID: {pid}) as {filename}")
            result[filename] = ImportExportClient(src_host=src_host, src_token=src_token).export_project(
                project, dry_run=self.dry_run)
            if self.retain_contributors and not self.config.direct_transfer:
                self.log.info(
                    f"{dry_log}Contributor Retention is enabled. Project export is complete Removing all project contributors from members")
                c_retention.remove_contributors_from_project(source=True)
            if not self.dry_run:
                if self.config.airgap:
                    exported_features = self.export_single_project_features(
                        project, src_host, src_token)
                    result[filename] = {
                        'exported': True,
                        'exported_features': exported_features
                    }
                    final_path = create_archive(
                        pid, f"{self.config.filesystem_path}/downloads/{filename}")
                    self.log.info(
                        f"Saved project [{project_path}:{pid}] archive to {final_path}")
                    delete_project_features(pid)

                # Archive project immediately after export, if exported
                if self.config.archive_logic and result[filename]:
                    self.log.info(
                        f"Archiving source project '{project_path}' (ID: {pid})")
                    self.projects_api.archive_project(
                        self.config.source_host, self.config.source_token, pid)
        except (IOError, RequestException) as oe:
            self.log.error(
                f"Failed to export/download project {project_path} (ID: {pid}) as {filename} with error:\n{oe}")
        except Exception as e:
            self.log.error(e)
            self.log.error(print_exc())
        return result

    def handle_importing_projects(self, project, dst_host=None, dst_token=None, group_path=None, filename=None):
        src_id = project["id"]
        path = project["path_with_namespace"]
        dst_host = dst_host or self.config.destination_host
        dst_token = dst_token or self.config.destination_token
        src_host = self.config.source_host
        src_token = self.config.source_token
        archived = False if self.config.airgap else self.projects_api.get_project_archive_state(
            src_host, src_token, src_id)
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
                    ie_client = ImportExportClient(
                        dest_host=dst_host, dest_token=dst_token)
                    import_id = ie_client.import_project(
                        project, dry_run=self.dry_run, group_path=group_path or tn)
                if import_id and not self.dry_run:
                    # Store project ID mapping
                    self.project_id_mapping[src_id] = import_id

                    # Disable Shared CI
                    self.disable_shared_ci(dst_pwn, import_id)

                    # Post import features
                    self.log.info(
                        f"Migrating additional source project '{path}' (ID: {src_id}) GitLab features")

                    # Certain project features cannot be migrated when archived
                    if archived and not self.config.airgap:
                        self.log.info(
                            f"Unarchiving source project '{path}' (ID: {src_id})")
                        self.projects_api.unarchive_project(
                            src_host, src_token, src_id)

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
        finally:
            if not self.dry_run:
                if archived and not self.config.airgap:
                    self.projects_api.archive_project(
                        src_host, src_token, src_id,
                        message=f"Archiving back source project '{path}' (ID: {src_id})")
                # Archive project immediately after import, if imported
                elif self.config.archive_logic and import_id:
                    self.projects_api.archive_project(
                        src_host, src_token, src_id,
                        message=f"Archiving active source project '{path}' (ID: {src_id})")

                if self.config.airgap:
                    self.log.info(f"Deleting project export file {filename}")
                    delete_project_export(filename)

                # Write project id mapping file
                self.write_project_id_mapping_file()
        return result

    def migrate_single_project_features(self, project, dst_id, dest_host=None, dest_token=None):
        """
            Subsequent function to update project info AFTER import
        """
        project.pop("members", None)
        src_id = project["id"]
        src_path = project["path_with_namespace"]
        shared_with_groups = project["shared_with_groups"]
        jobs_enabled = project["jobs_enabled"]
        results = {}

        results["id"] = dst_id

        # Set default branch
        self.branches.set_branch(src_path, dst_id, project["default_branch"])

        # Shared with groups
        results["shared_with_groups"] = self.projects.add_shared_groups(
            dst_id, src_path, shared_with_groups)

        # Environments
        results["environments"] = EnvironmentsClient(dest_host=dest_host, dest_token=dest_token).migrate_project_environments(
            src_id, dst_id, src_path, jobs_enabled)

        vars_client = VariablesClient(
            dest_host=dest_host, dest_token=dest_token)
        # CI/CD Variables
        results["cicd_variables"] = vars_client.migrate_cicd_variables(
            src_id, dst_id, src_path, "projects", jobs_enabled)

        # Pipeline Schedule Variables
        results["pipeline_schedule_variables"] = vars_client.migrate_pipeline_schedule_variables(
            src_id, dst_id, src_path, jobs_enabled)

        if not self.config.airgap:
            # Deploy Keys
            results["deploy_keys"] = self.keys.migrate_project_deploy_keys(
                src_id, dst_id, src_path)

            # Container Registries
            if self.config.source_registry and self.config.destination_registry:
                results["container_registry"] = self.registries.migrate_registries(
                    project, dst_id)

            # Package Registries
            if not project.get("packages_enabled", True):
                self.log.info(f"Skipping package migration for project '{project['path_with_namespace']}' because packages are disabled.")
            else:
                results["package_registry"] = self.packages.migrate_project_packages(
                    src_id, dst_id, src_path
                )

            # Hooks (Webhooks)
            results["project_hooks"] = self.hooks.migrate_project_hooks(
                src_id, dst_id, src_path)

            # Project Feature Flag Users Lists
            project_feature_flags_users_lists = self.project_feature_flags_users_lists_client.migrate_project_feature_flags_user_lists_for_project(
                src_id, dst_id)
            results["project_feature_flags_users_lists"] = project_feature_flags_users_lists.get('completed')

            # Project Feature Flags
            results["project_feature_flags"] = self.project_feature_flags_client.migrate_project_feature_flags_for_project(
                src_id, dst_id, project_feature_flags_users_lists.get('user_lists_conversion_list') if isinstance(project_feature_flags_users_lists, dict) else None)

        if self.config.source_tier not in ["core", "free"]:
            # Push Rules - handled by GitLab Importer as of 13.6
            results["push_rules"] = self.pushrules.migrate_push_rules(
                src_id, dst_id, src_path)

            # Merge Request Approvals
            results["project_level_mr_approvals"] = MergeRequestApprovalsClient(dest_host=dest_host, dest_token=dest_token).migrate_project_level_mr_approvals(
                src_id, dst_id, src_path)

        # Source fields
        results["src_id"] = src_id
        results["src_path"] = src_path
        results["src_url"] = project["http_url_to_repo"]

        if self.config.remapping_file_path:
            self.projects.migrate_gitlab_variable_replace_ci_yml(dst_id)

        c_retention = None
        if self.retain_contributors and not self.config.direct_transfer:
            self.log.info(
                f"Contributor Retention is enabled. Project {project['path_with_namespace']} has been imported so removing all project contributors as project members")
            c_retention = ContributorRetentionClient(
                src_id, dst_id, project['path_with_namespace'], dry_run=self.dry_run)
            c_retention.build_map()
            c_retention.remove_contributors_from_project()

        self.remove_import_user(dst_id, host=dest_host, token=dest_token)
        if self.config.airgap:
            delete_project_features(src_id)

        if self.config.direct_transfer and self.config.archive_logic:
            self.log.info(
                f"Archiving active source project '{src_path}' (ID: {src_id})")
            self.projects_api.archive_project(
                self.config.source_host, self.config.source_token, src_id)
        self.log.info(
            f"Completed migrating additional source project '{src_path}' (ID: {src_id}) GitLab features")
        return results

    def export_single_project_features(self, project, src_host, src_token):
        """
            Function to export project features to mongo to then package up into a tar
        """
        path_with_namespace = project["path_with_namespace"]
        src_id = project["id"]
        jobs_enabled = project.get("jobs_enabled", False)
        results = {}

        self.log.info(f"Exporting project '{path_with_namespace}' (ID: {src_id}) (features")

        mongo = CongregateMongoConnector()
        mongo.create_collection_with_unique_index('project_features', 'id')
        mongo.db['project_features'].insert_one(SingleProjectFeatures(
            id=src_id,
            project_details=from_dict(ProjectDetails, project)
        ).to_dict())
        mongo.close_connection()
        project.pop("members", None)

        # Environments
        results["environments"] = EnvironmentsClient(src_host=src_host, src_token=src_token).migrate_project_environments(
            src_id, None, path_with_namespace, jobs_enabled)

        vars_client = VariablesClient(
            src_host=src_host, src_token=src_token)
        # CI/CD Variables
        results["cicd_variables"] = vars_client.migrate_cicd_variables(
            src_id, None, path_with_namespace, "projects", jobs_enabled)

        # Pipeline Schedule Variables
        results["pipeline_schedule_variables"] = vars_client.migrate_pipeline_schedule_variables(
            src_id, None, path_with_namespace, jobs_enabled)

        if self.config.source_tier not in ["core", "free"]:
            # Merge Request Approvals
            results["project_level_mr_approvals"] = MergeRequestApprovalsClient(
                src_host=src_host, src_token=src_token).migrate_project_level_mr_approvals(
                src_id, None, path_with_namespace)

        return results

    def migrate_linked_items_in_issues(self):
        # Read the mapping file from the json and put it inside the project_id_mapping variable
        project_id_mapping = mig_utils.get_project_id_mapping()
        # Migrate issue links
        self.issue_links_client.migrate_issue_links(project_id_mapping)

    def write_project_id_mapping_file(self):
        write_json_to_file(
            f"{self.app_path}/data/project_id_mapping.json", self.project_id_mapping)


@shared_task
def export_task(project: dict, host: str, token: str):
    client = GitLabMigrateClient(dry_run=False, skip_users=True,
                                 skip_groups=True, skip_project_import=True)
    return client.handle_exporting_projects(project, src_host=host, src_token=token)


@shared_task
def import_task(file_path: str, group: dict, host: str, token: str):
    client = GitLabMigrateClient(dry_run=False, skip_users=True,
                                 skip_groups=True, skip_project_import=True)
    project_features, export_filename = extract_archive(file_path)

    return client.handle_importing_projects(project_features, dst_host=host, dst_token=token,
                                            group_path=group['full_path'], filename=export_filename)


@shared_task(name='post-migration-task')
@mongo_connection
def post_migration_task(entity, dest_host, dest_token, mongo=None, dry_run=True):
    # In the event a direct transfer entity import fails, the entity parameter could be None
    # and then we will need to skip doing any post migration tasks
    if entity:
        client = GitLabMigrateClient(dry_run=dry_run, skip_users=True,
                                     skip_groups=True, skip_project_import=True)
        entity = from_dict(data_class=BulkImportEntityStatus, data=entity)
        if entity.entity_type == "project":
            project_col = f"projects-{strip_netloc(client.config.source_host)}"
            source_project = mongo.safe_find_one(project_col, {
                'path_with_namespace': entity.source_full_path
            })
            return client.migrate_single_project_features(
                source_project, entity.project_id, dest_host=dest_host, dest_token=dest_token)
        if entity.entity_type == "group":
            group_col = f"groups-{strip_netloc(client.config.source_host)}"
            source_group = mongo.safe_find_one(group_col, {
                'full_path': entity.source_full_path
            })
            if source_group:
                return client.migrate_single_group_features(
                    source_group['id'], entity.namespace_id, entity.destination_full_path)
            print(
                f"source_group was None. It could not be found in the {group_col} collection using the full_path of {entity.source_full_path}. entity object is {entity}")
            return False
    else:
        return False
