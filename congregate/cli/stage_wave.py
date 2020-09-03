"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

from congregate.helpers.misc_utils import rewrite_list_into_dict
from congregate.migration.meta.etl import WaveSpreadsheetHandler
from congregate.cli.stage_base import BaseStageClass
from congregate.cli.stage_projects import ProjectStageCLI

class WaveStageCLI(BaseStageClass):
    def __init__(self):
        self.pcli = ProjectStageCLI()
        super(WaveStageCLI, self).__init__()

    def stage_wave(self, wave_to_stage, dry_run=True):
        ids_to_stage = self.get_ids_to_stage_wave(wave_to_stage)
        self.pcli.stage_data(ids_to_stage, dry_run=dry_run)

    def get_ids_to_stage_wave(self, wave_to_stage, dry_run=True):
        projects = rewrite_list_into_dict(self.open_projects_file(), "http_url_to_repo")
        wsh = WaveSpreadsheetHandler(self.config.wave_spreadsheet_path, columns_to_use=self.config.wave_spreadsheet_columns)
        wave_data = wsh.read_file_as_json(
            df_filter=(
                self.config.wave_spreadsheet_column_mapping["Wave name"], wave_to_stage))
        ids_to_stage = []
        for w in wave_data:
            url_key = self.config.wave_spreadsheet_column_mapping["Source Url"]
            if projects.get(w[url_key], None):
                ids_to_stage.append(str(projects[w[url_key]]["id"]))
        
        return ids_to_stage
        
