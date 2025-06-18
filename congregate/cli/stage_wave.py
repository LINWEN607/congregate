"""
Congregate - GitLab instance migration utility

Copyright (c) 2022 - GitLab
"""
import os
import sys

from gitlab_ps_utils.misc_utils import get_dry_log, safe_json_response
from gitlab_ps_utils.dict_utils import rewrite_list_into_dict, dig
from gitlab_ps_utils.string_utils import clean_split
from gitlab_ps_utils.list_utils import remove_dupes
from gitlab_ps_utils.json_utils import json_pretty

from congregate.migration.meta.etl import WaveSpreadsheetHandler
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.cli.stage_base import BaseStageClass
from congregate.cli.stage_projects import ProjectStageCLI
from congregate.helpers.utils import is_dot_com
from congregate.helpers.migrate_utils import get_staged_user_projects


class WaveStageCLI(BaseStageClass):
    def __init__(self):
        self.pcli = ProjectStageCLI()
        self.groups_api = GroupsApi()
        super().__init__()

    def parent_path_fail(self, parent_path):
        self.log.error(
            f"'Parent Path' column missing or misspelled ({parent_path}). Exiting...")
        sys.exit(os.EX_CONFIG)

    def stage_data(self, wave_to_stage, dry_run=True,
                   skip_users=False, scm_source=None):
        self.stage_wave(wave_to_stage, skip_users=False, dry_run=dry_run, scm_source=scm_source)
        if user_projects := get_staged_user_projects(
                remove_dupes(self.staged_projects)):
            self.log.warning(
                f"USER projects staged (Count : {len(user_projects)}):\n{json_pretty(user_projects)}")
            if is_dot_com(self.config.destination_host):
                self.log.warning(
                    "Please manually migrate USER projects to gitlab.com")
        # Direct-transfer uses Placeholder users
        if self.config.source_type == "gitlab" and not self.config.direct_transfer:
            self.are_staged_users_without_public_email()
        if not dry_run:
            self.write_staging_files(skip_users=skip_users)

    def stage_wave(self, wave_to_stage, skip_users=False, dry_run=True, scm_source=None):
        """
        Gets all IDs of repos from specific wave listed in wave stage spreadsheet

        Relies on mapping a git repo URL in the spreadsheet to http_url_to_repo in projects.json to get the IDs

        :param wave_to_stage: The name of the wave from the spreadsheet to stage
        :param dry_run: Optional parameter. Default True
        :return: List of IDs cast to strings to be used by ProjectStageCLI
        """
        i = 0
        if scm_source is not None:
            i = self.the_number_of_instance(scm_source)
        if i == -1:
            self.log.warning(
                f"Couldn't find the correct GH instance with hostname: {scm_source}")
        self.rewritten_projects = rewrite_list_into_dict(
            self.open_projects_file(scm_source), "id")
        self.rewritten_users = rewrite_list_into_dict(
            self.open_users_file(scm_source), "id")
        self.rewritten_groups = rewrite_list_into_dict(
            self.open_groups_file(scm_source), "id")
        self.group_paths = rewrite_list_into_dict(
            self.open_groups_file(scm_source), "full_path", lowercase=True)
        self.project_urls = rewrite_list_into_dict(
            self.open_projects_file(scm_source), "http_url_to_repo", lowercase=True)
        self.project_paths = rewrite_list_into_dict(
            self.open_projects_file(scm_source), "path_with_namespace", lowercase=True)
        unable_to_find = []

        wave_spreadsheet_path = self.config.wave_spreadsheet_path
        if not os.path.isfile(wave_spreadsheet_path):
            self.log.error(
                f"Config 'wave_spreadsheet_path' file path '{wave_spreadsheet_path}' does not exist. Please create it")
            sys.exit(os.EX_CONFIG)

        wsh = WaveSpreadsheetHandler(
            wave_spreadsheet_path,
            columns_to_use=self.config.wave_spreadsheet_columns
        )
        # Simplifying the variable name, for readability.
        column_mapping = self.config.wave_spreadsheet_column_mapping

        # This is reading the actual spreadsheet, filtering it to the desired
        # stage
        wave_data = wsh.read_file_as_json(
            df_filter=(
                "Wave Name",
                wave_to_stage
            )
        )
        if not wave_data:
            self.log.error(
                f"No rows for wave {wave_to_stage} found in '{wave_spreadsheet_path}' spreadsheet.")
            sys.exit(os.EX_CONFIG)

        # Some basic sanity checks for reading in spreadsheet data
        self.check_spreadsheet_data()
        # Iterating over a spreadsheet row
        ids_to_stage = []
        for row in wave_data:
            # At this point, we should only have the relevant wave rows
            # We can collect the Project IDs at this time to use for staging
            # with ProjectStageCLI
            if not row.get("Override"):
                ids_to_stage.append(str((row.get("Source Project ID"))))
            else:
                # We currently use a additional field in the project entity called target_namespace
                # that determines where a group or project will land (basically, full path to its parent)
                # In conjunction with the Override flag, we determine if we should add the target_namespace
                # and honor it or not
                # How this conflicts is in some of our downstream computation of full_path, path_with_namespace
                # and other fields that determine where to look on source and destination for existence
                # and for moving items. The checks themselves can be inconsistent and layered, and don't all account
                # for Override scenarios
                # We need to streamline the way we determine the destination and the source to work consistently in the base case
                # but use target_namespace if it exists
                self.log.error(
                    f"OVERRIDE is flagged True for row {row}. Feature is currently not implemented. Row will not be staged for migration.")

        self.pcli.stage_data(ids_to_stage, dry_run=dry_run, skip_users=skip_users, scm_source=scm_source)

    def check_spreadsheet_data(self):
        '''
        Check the spreadsheet against the values in the config file,
        return true if all good, warn if not.
        '''
        if not (mapping := self.config.wave_spreadsheet_column_to_project_property_mapping):
            self.log.warning(
                "No 'wave_spreadsheet_column_to_project_property_mapping' field in congregate.conf")
        if not (columns := self.config.wave_spreadsheet_columns):
            self.log.warning(
                "No 'wave_spreadsheet_columns' field in congregate.conf")
        if not self.check_spreadsheet_kv(mapping, columns):
            self.log.warning(
                "Mismatch between keys in wave_spreadsheet_columns and wave_spreadsheet_column_to_project_property_mapping"
            )

    def check_spreadsheet_kv(self, mapping, columns):
        '''
        make sure each item in mapping exists in columns.
        '''
        i = 0
        for item in mapping:
            if mapping[item] in columns:
                i += 1
        return i == len(mapping)

    def append_project_data(self, project, projects_to_stage,
                            wave_row, p_range=0, dry_run=True):
        for member in project["members"]:
            self.append_member_to_members_list([], member, dry_run)

        p_id = project["id"]
        p_path = project['path_with_namespace']
        p_type = project["project_type"]
        try:
            if p_type == "group" or (p_type == "user" and not is_dot_com(self.config.destination_host)):
                if parent_group_id := dig(self.rewritten_projects.get(p_id), "namespace", "id"):
                    if group_to_stage := self.rewritten_groups.get(parent_group_id):
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging group {group_to_stage['full_path']} (ID: {group_to_stage['id']})")
                        self.handle_parent_group(wave_row, group_to_stage)
                        self.staged_groups.append(
                            self.format_group(group_to_stage))

                        # Append all group members to staged users
                        for member in group_to_stage["members"]:
                            self.append_member_to_members_list(
                                [], member, dry_run)
                    else:
                        self.log.warning(
                            f"Project '{p_path}' ({p_id}) parent group ID {parent_group_id} NOT found among listed groups")
                    self.log.info(
                        f"{get_dry_log(dry_run)}Staging {p_type} project '{p_path}' (ID: {p_id})"
                        f"[{len(self.staged_projects) + 1}/{len(p_range) if p_range else len(projects_to_stage)}]")
                    self.staged_projects.append(project)
                else:
                    self.log.warning(
                        f"Project '{p_path}' ({p_id}) NOT found among listed projects")
            else:
                self.log.warning(
                    f"Please manually migrate '{p_type}' project '{p_path}' ({p_id}) to gitlab.com")
        except Exception as e:
            self.log.error(
                f"Failed to append project '{p_path}' ({p_id}) to staged projects:\n{e}")
            sys.exit(os.EX_DATAERR)

    def append_group_data(self, group, groups_to_stage,
                          wave_row, p_range=0, dry_run=True):
        # Append all group projects to staged projects
        for pid in group.get("projects", []):
            obj = self.get_project_metadata(pid, group=True)
            if parent_path := self.config.wave_spreadsheet_column_mapping.get(
                    "Parent Path"):
                obj["target_namespace"] = wave_row[parent_path].strip("/")
                if wave_row.get("SWC AA ID"):
                    obj['swc_manager_name'] = wave_row.get('SWC Manager Name')
                    obj['swc_manager_email'] = wave_row.get(
                        'SWC Manager Email')
                    obj['swc_id'] = wave_row.get('SWC AA ID')
                else:
                    self.log.info(
                        f"No 'SWC AA ID' (SWC_ID) provided for {obj['target_namespace']}")
            else:
                self.parent_path_fail(parent_path)
            # Append all project members to staged users
            for project_member in obj["members"]:
                self.append_member_to_members_list([], project_member, dry_run)
            self.log.info(
                f"{get_dry_log(dry_run)}Staging project {obj['path_with_namespace']} (ID: {obj['id']})")
            self.staged_projects.append(obj)

        self.log.info(
            f"{get_dry_log(dry_run)}Staging group {group['full_path']} (ID: {group['id']})"
            f"[{len(self.staged_groups) + 1}/{len(p_range) if p_range else len(groups_to_stage)}]"
        )
        group.pop("projects", None)
        self.staged_groups.append(group)

        # Append all group members to staged users
        for member in group["members"]:
            self.append_member_to_members_list([], member, dry_run)

    def append_parent_group_full_path(self, full_path, wave_row, parent_path):
        if wave_path := wave_row.get(parent_path):
            if wave_row.get("Override"):
                return wave_path or full_path
            if len(set(full_path.split("/")) -
                    set(wave_path.split("/"))) <= 1:
                return f"{wave_path}/{full_path}".strip("/")
        self.log.warning(
            f"No 'Parent Path' value defined ({wave_path}). Defaulting 'full_path' to '{full_path}'")
        return full_path

    def get_parent_id(self, wave_row, parent_path):
        if full_path := wave_row.get(parent_path, ""):
            if req := safe_json_response(self.groups_api.get_group_by_full_path(
                    full_path.lstrip("/"),
                    self.config.destination_host,
                    self.config.destination_token)):
                return req.get("id")
        self.log.warning(
            f"No 'Parent Path' value defined ({full_path}). Defaulting `parent_id` to 'null'")
        return None

    def handle_parent_group(self, wave_row, group):
        parent_path = "Target Namespace"
        group["full_path"] = self.append_parent_group_full_path(
            group["full_path"], wave_row, parent_path)
        group["parent_id"] = self.get_parent_id(wave_row, parent_path)

    def sanitize_project_path(self, http_url_to_repo, host=""):
        host = host if host else self.config.source_host
        return http_url_to_repo.rstrip(
            "/").split(host)[-1].lstrip("/").strip(" ")

    def find_group(self, repo_url):
        group_path = repo_url.rstrip("/").split("/")[-1]
        if group := self.group_paths.get(group_path):
            if len(clean_split(repo_url, group_path, 1)) == 1:
                return group
            self.log.warning(
                f"Possible invalid group {repo_url} found. Review spreadsheet.")
        return None
