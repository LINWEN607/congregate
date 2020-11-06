"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

from congregate.helpers.misc_utils import rewrite_list_into_dict, get_dry_log, safe_json_response
from congregate.migration.meta.etl import WaveSpreadsheetHandler
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.cli.stage_base import BaseStageClass
from congregate.cli.stage_projects import ProjectStageCLI

class WaveStageCLI(BaseStageClass):
    def __init__(self):
        self.pcli = ProjectStageCLI()
        self.groups_api = GroupsApi()
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
        groups = rewrite_list_into_dict(self.open_groups_file(), "full_path")
        projects = rewrite_list_into_dict(self.open_projects_file(), "http_url_to_repo")
        project_paths = rewrite_list_into_dict(self.open_projects_file(), "path_with_namespace")
        wsh = WaveSpreadsheetHandler(self.config.wave_spreadsheet_path, columns_to_use=self.config.wave_spreadsheet_columns)
        wave_data = wsh.read_file_as_json(
            df_filter=(
                self.config.wave_spreadsheet_column_mapping["Wave name"], wave_to_stage))
        for w in wave_data:
            url_key = self.config.wave_spreadsheet_column_mapping["Source Url"]
            if project := (projects.get(w[url_key], None) or project_paths.get(w[url_key].rstrip("/").split(self.config.source_host)[-1].lstrip("/"))):
                obj = self.get_project_metadata(project)
                if parent_path := self.config.wave_spreadsheet_column_mapping.get("Parent Path"):
                    obj["target_namespace"] = w[parent_path]
                self.append_project_data(obj, wave_data, w)
            elif group := groups.get(w[url_key].rstrip("/").split("/")[-1]):
                if parent_path := self.config.wave_spreadsheet_column_mapping.get("Parent Path"):
                    group["full_path"] = f"{w[parent_path]}/{group['full_path']}"
                self.handle_parent_group(w, group)
                self.append_group_data(group, wave_data, w)
    
    def append_project_data(self, project, projects_to_stage, wave_row, p_range=0, dry_run=True):
        for member in project["members"]:
            self.append_member_to_members_list([], member, dry_run)

        if project["project_type"] == "group":
            group_to_stage = self.rewritten_groups[self.rewritten_projects.get(project["id"])["namespace"]["id"]]
            self.log.info("{0}Staging group {1} (ID: {2})".format(get_dry_log(
                dry_run), group_to_stage["full_path"], group_to_stage["id"]))
            group_to_stage.pop("projects", None)
            self.handle_parent_group(wave_row, group_to_stage)
            self.staged_groups.append(group_to_stage)

            # Append all group members to staged users
            for member in group_to_stage["members"]:
                self.append_member_to_members_list([], member, dry_run)

        self.log.info("{0}Staging project {1} (ID: {2}) [{3}/{4}]".format(get_dry_log(
            dry_run), project["path_with_namespace"], project["id"], len(self.staged_projects) + 1, len(p_range) if p_range else len(projects_to_stage)))
        self.staged_projects.append(project)
    
    def append_group_data(self, group, groups_to_stage, wave_row, p_range=0, dry_run=True):
        # Append all group projects to staged projects
        for project in group["projects"]:
            obj = self.get_project_metadata(project)
            if parent_path := self.config.wave_spreadsheet_column_mapping.get("Parent Path"):
                obj["target_namespace"] = wave_row[parent_path].strip("/")
            # Append all project members to staged users
            for project_member in obj["members"]:
                self.append_member_to_members_list([], project_member, dry_run)
            self.log.info("{0}Staging project {1} (ID: {2})".format(
                get_dry_log(dry_run), obj["path_with_namespace"], obj["id"]))
            self.staged_projects.append(obj)

        self.log.info("{0}Staging group {1} (ID: {2}) [{3}/{4}]".format(get_dry_log(
            dry_run), group["full_path"], group["id"], len(self.staged_groups) + 1, len(p_range) if p_range else len(groups_to_stage)))
        group.pop("projects", None)
        self.staged_groups.append(group)

        # Append all group members to staged users
        for member in group["members"]:
            self.append_member_to_members_list([], member, dry_run)

    def append_parent_group_full_path(self, group, wave_row, parent_path):
        if wave_row[parent_path] not in group["full_path"]:
            return f"{wave_row[parent_path]}/{group['full_path']}"
        return group["full_path"]
    
    def get_parent_id(self, wave_row, parent_path):
        if req := safe_json_response(self.groups_api.get_group_by_full_path(wave_row[parent_path].lstrip("/"), 
                                        self.config.destination_host, 
                                        self.config.destination_token)):
            return req.get("id")
    
    def handle_parent_group(self, wave_row, group):
        if parent_path := self.config.wave_spreadsheet_column_mapping.get("Parent Path"):
            group["full_path"] = self.append_parent_group_full_path(group, wave_row, parent_path)
            group["parent_id"] = self.get_parent_id(wave_row, parent_path)
