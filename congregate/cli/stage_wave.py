"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

import json
import re

from congregate.helpers.misc_utils import get_dry_log, remove_dupes, rewrite_list_into_dict
from congregate.migration.meta.etl import WaveSpreadsheetHandler
from congregate.cli.stage_base import BaseStageClass

class WaveStageCLI(BaseStageClass):

    def stage_wave(self, wave_to_stage, dry_run=True):
        projects = rewrite_list_into_dict(self.open_projects_file(), "http_url_to_repo")
        wsh = WaveSpreadsheetHandler(self.config.wave_spreadsheet_path, columns_to_use=self.config.wave_spreadsheet_columns)
        wave_data = wsh.read_file_as_json(
            df_filter=(
                self.config.wave_spreadsheet_column_mapping["Wave name"], wave_to_stage))
        ids_to_stage = []
        for w in wave_data:
            url_key = self.config.wave_spreadsheet_column_mapping["Source Url"]
            if projects.get(w[url_key], None):
                ids_to_stage.append(projects[w[url_key]])
        
        return ids_to_stage
        
