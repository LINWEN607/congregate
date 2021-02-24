"""
Congregate - GitLab instance migration utility

Copyright (c) 2021 - GitLab
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
        super().__init__()

    def stage_data(self, wave_to_stage, dry_run=True,
                   skip_users=False, scm_source=None):
        self.stage_wave(wave_to_stage, dry_run, scm_source)
        if not dry_run:
            self.write_staging_files(skip_users=skip_users)

    def stage_wave(self, wave_to_stage, dry_run=True, scm_source=None):
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
        groups = rewrite_list_into_dict(
            self.open_groups_file(scm_source), "full_path", lowercase=True)
        projects = rewrite_list_into_dict(
            self.open_projects_file(scm_source), "http_url_to_repo", lowercase=True)
        project_paths = rewrite_list_into_dict(
            self.open_projects_file(scm_source), "path_with_namespace", lowercase=True)
        unable_to_find = []
        wsh = WaveSpreadsheetHandler(
            self.config.wave_spreadsheet_path,
            columns_to_use=self.config.wave_spreadsheet_columns
        )
        # Simplifying the variable name, for readability.
        column_mapping = self.config.wave_spreadsheet_column_mapping
        # This is reading the actual spreadsheet, filtering it to the desired
        # stage
        wave_data = wsh.read_file_as_json(
            df_filter=(
                column_mapping["Wave name"],
                wave_to_stage
            )
        )
        # Some basic sanity checks for reading in spreadsheet data
        self.check_spreadsheet_data()
        # Iterating over a spreadsheet row
        for row in wave_data:
            url_key = column_mapping["Source Url"]
            repo_url = row.get(url_key, "").lower()
            if project := (projects.get(repo_url, None) or (projects.get(repo_url + 'git', None))
                           or project_paths.get(self.sanitize_project_path(repo_url, host=scm_source))):
                obj = self.get_project_metadata(project)
                if parent_path := column_mapping.get("Parent Path"):
                    obj["target_namespace"] = row[parent_path].strip("/")
                    if row.get("SWC AA ID"):
                        obj['swc_manager_name'] = row.get('SWC Manager Name')
                        obj['swc_manager_email'] = row.get('SWC Manager Email')
                        obj['swc_id'] = row.get('SWC AA ID')
                    else:
                        self.log.warning(f"No SWC_ID for {obj['target_namespace']}")
                self.append_project_data(obj, wave_data, row, dry_run=dry_run)
            elif group := groups.get(repo_url.rstrip("/").split("/")[-1]):
                group_copy = group.copy()
                self.handle_parent_group(row, group_copy)
                self.append_group_data(
                    group_copy, wave_data, row, dry_run=dry_run)
            else:
                self.log.warning(f"Unable to find {repo_url} in listed data")
                unable_to_find.append(repo_url)

        if unable_to_find:
            self.log.warning("The following data was not found:\n{}".format(
                "\n".join(unable_to_find)))

    def check_spreadsheet_data(self):
        '''
        Check the spreadsheet against the values in the config file,
        return true if all good, warn if not.
        '''
        if not (mapping := self.config.wave_spreadsheet_column_mapping):
            self.log.warning(
                "We didn't find a wave_spreadsheet_column_mapping in congregate.conf")
        if not (columns := self.config.wave_spreadsheet_columns):
            self.log.warning(
                "We didn't find a wave_spreadsheet_columns in congregate.conf")
        if not self.check_spreadsheet_lengths(mapping, columns):
            self.log.warning(
                "The length of wave_spreadsheet_columns didn't match "
                "wave_spreadsheet_column_mapping in congregate.conf"
            )
        if not self.check_spreadsheet_kv(mapping, columns):
            self.log.warning(
                "Mismatch between keys in wave_spreadsheet_columns and wave_spreadsheet_column_mapping"
            )

    def check_spreadsheet_kv(self, mapping, columns):
        '''
        make sure each item in columns list exists in mapping dictionary.
        '''
        i = 0
        for item in mapping:
            if mapping[item] in columns:
                i += 1
        if i == len(mapping):
            return True

    def check_spreadsheet_lengths(self, mapping, columns):
        '''
        Compare the lengths of columns and mappings, return True if == False if not
        '''

        return len(mapping) == len(columns)

    def append_project_data(self, project, projects_to_stage,
                            wave_row, p_range=0, dry_run=True):
        for member in project["members"]:
            self.append_member_to_members_list([], member, dry_run)

        if project["project_type"] == "group":
            group_to_stage = self.rewritten_groups[self.rewritten_projects.get(project["id"])[
                "namespace"]["id"]].copy()
            self.log.info("{0}Staging group {1} (ID: {2})".format(get_dry_log(
                dry_run), group_to_stage["full_path"], group_to_stage["id"]))
            group_to_stage.pop("projects", None)
            self.handle_parent_group(wave_row, group_to_stage)
            self.staged_groups.append(group_to_stage)

            # Append all group members to staged users
            for member in group_to_stage["members"]:
                self.append_member_to_members_list([], member, dry_run)

        self.log.info(
            f"{get_dry_log(dry_run)}Staging project {project['path_with_namespace']} (ID: {project['id']})"
            f"[{len(self.staged_projects) + 1}/{len(p_range) if p_range else len(projects_to_stage)}]"
        )
        self.staged_projects.append(project)

    def append_group_data(self, group, groups_to_stage,
                          wave_row, p_range=0, dry_run=True):
        # Append all group projects to staged projects
        for project in group.get("projects", []):
            obj = self.get_project_metadata(project)
            if parent_path := self.config.wave_spreadsheet_column_mapping.get(
                    "Parent Path"):
                obj["target_namespace"] = wave_row[parent_path].strip("/")
                if wave_row.get("SWC AA ID"):
                    obj['swc_manager_name'] = wave_row.get('SWC Manager Name')
                    obj['swc_manager_email'] = wave_row.get('SWC Manager Email')
                    obj['swc_id'] = wave_row.get('SWC AA ID')
                else:
                    self.log.warning(f"No SWC_ID for {obj['target_namespace']}")
            # Append all project members to staged users
            for project_member in obj["members"]:
                self.append_member_to_members_list([], project_member, dry_run)
            self.log.info("{0}Staging project {1} (ID: {2})".format(
                get_dry_log(dry_run), obj["path_with_namespace"], obj["id"]))
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
        if parent_path := self.config.wave_spreadsheet_column_mapping.get(
                "Parent Path"):
            if len(set(full_path.split("/")) -
                   set(parent_path.split("/"))) <= 1:
                return f"{wave_row[parent_path]}/{full_path}"
            return full_path

    def get_parent_id(self, wave_row, parent_path):
        if req := safe_json_response(self.groups_api.get_group_by_full_path(wave_row[parent_path].lstrip("/"),
                                                                            self.config.destination_host,
                                                                            self.config.destination_token)):
            return req.get("id")

    def handle_parent_group(self, wave_row, group):
        if parent_path := self.config.wave_spreadsheet_column_mapping.get(
                "Parent Path"):
            group["full_path"] = self.append_parent_group_full_path(
                group["full_path"], wave_row, parent_path)
            group["parent_id"] = self.get_parent_id(wave_row, parent_path)

    def sanitize_project_path(self, http_url_to_repo, host=""):
        host = host if host else self.config.source_host
        return http_url_to_repo.rstrip(
            "/").split(host)[-1].lstrip("/").strip(" ")
