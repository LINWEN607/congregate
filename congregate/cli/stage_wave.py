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
        self.stage_wave(wave_to_stage, skip_users=skip_users, dry_run=dry_run, scm_source=scm_source)
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

        wave_spreadsheet_path = self.config.wave_spreadsheet_path
        if not os.path.isfile(wave_spreadsheet_path):
            self.log.error(
                f"Config 'wave_spreadsheet_path' file path '{wave_spreadsheet_path}' does not exist. Please create it")
            sys.exit(os.EX_CONFIG)

        wsh = WaveSpreadsheetHandler(
            wave_spreadsheet_path,
            columns_to_use=self.config.wave_spreadsheet_columns
        )
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
                '''
                We currently use a additional field in the project entity called target_namespace
                that determines where a group or project will land (basically, full path to its parent)
                In conjunction with the Override flag, we determine if we should add the target_namespace
                and honor it or not
                How this conflicts is in some of our downstream computation of full_path, path_with_namespace
                and other fields that determine where to look on source and destination for existence
                and for moving items. The checks themselves can be inconsistent and layered, and don't all account
                for Override scenarios
                We need to streamline the way we determine the destination and the source to work consistently in the base case
                but use target_namespace if it exists
                '''
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
            return
        if not (columns := self.config.wave_spreadsheet_columns):
            self.log.warning(
                "No 'wave_spreadsheet_columns' field in congregate.conf")
            return
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
            if item in columns:
                i += 1
        return i == len(mapping)
