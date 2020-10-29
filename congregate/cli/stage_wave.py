"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

from congregate.helpers.misc_utils import rewrite_list_into_dict, get_dry_log
from congregate.migration.meta.etl import WaveSpreadsheetHandler
from congregate.cli.stage_base import BaseStageClass
from congregate.cli.stage_projects import ProjectStageCLI

class WaveStageCLI(BaseStageClass):
    def __init__(self):
        self.pcli = ProjectStageCLI()
        super(WaveStageCLI, self).__init__()

    def stage_data(self, wave_to_stage, dry_run=True, skip_users=False):
        self.stage_wave(wave_to_stage)
        if not dry_run:
            self.write_staging_files(skip_users=skip_users)

    def stage_wave(self, wave_to_stage):
        """
        Gets all IDs of repos from specific wave listed in wave stage spreadsheet

        Relies on mapping a git repo URL in the spreadsheet to http_url_to_repo in project_json.json to get the IDs

        :param wave_to_stage: The name of the wave from the spreadsheet to stage
        :param dry_run: Optional parameter. Default True
        :return: List of IDs cast to strings to be used by ProjectStageCLI
        """
        self.rewritten_projects = rewrite_list_into_dict(self.open_projects_file(), "id")
        self.rewritten_users = rewrite_list_into_dict(self.open_users_file(), "id")
        self.rewritten_groups = rewrite_list_into_dict(self.open_groups_file(), "id")
        projects = rewrite_list_into_dict(self.open_projects_file(), "http_url_to_repo")
        wsh = WaveSpreadsheetHandler(self.config.wave_spreadsheet_path, columns_to_use=self.config.wave_spreadsheet_columns)
        wave_data = wsh.read_file_as_json(
            df_filter=(
                self.config.wave_spreadsheet_column_mapping["Wave name"], wave_to_stage))
        for w in wave_data:
            url_key = self.config.wave_spreadsheet_column_mapping["Source Url"]
            if project := projects.get(w[url_key], None):
                obj = self.get_project_metadata(project)
                if parent_path := self.config.wave_spreadsheet_column_mapping.get("Parent Path"):
                    obj["target_namespace"] = w[parent_path]
                self.append_data(obj, wave_data)
    
    def append_data(self, project, projects_to_stage, p_range=0, dry_run=True):
        for member in project["members"]:
            self.append_member_to_members_list([], member, dry_run)

        if project["project_type"] == "group":
            print(project)
            group_to_stage = self.rewritten_groups[self.rewritten_projects.get(project["id"])["namespace"]["id"]]
            self.log.info("{0}Staging group {1} (ID: {2})".format(get_dry_log(
                dry_run), group_to_stage["full_path"], group_to_stage["id"]))
            group_to_stage.pop("projects", None)
            self.staged_groups.append(group_to_stage)

            # Append all group members to staged users
            for member in group_to_stage["members"]:
                self.append_member_to_members_list([], member, dry_run)

        self.log.info("{0}Staging project {1} (ID: {2}) [{3}/{4}]".format(get_dry_log(
            dry_run), project["path_with_namespace"], project["id"], len(self.staged_projects) + 1, len(p_range) if p_range else len(projects_to_stage)))
        self.staged_projects.append(project)