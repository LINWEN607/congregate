import unittest
import mock
from congregate.cli.stage_wave import WaveStageCLI
from congregate.cli.stage_base import BaseStageClass
from congregate.migration.meta.etl import WaveSpreadsheetHandler
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.users import MockUsersApi


class StageWaveTests(unittest.TestCase):
    def setUp(self):
        self.projects_api = MockProjectsApi()
        self.groups_api = MockGroupsApi()
        self.users_api = MockUsersApi()
        self.mock = mock.MagicMock()
        self.wcli = WaveStageCLI()

    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_columns', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_column_mapping', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_path', new_callable=mock.PropertyMock)
    @mock.patch.object(WaveSpreadsheetHandler, "read_file_as_json")
    @mock.patch.object(BaseStageClass, "open_projects_file")
    def test_get_ids_to_stage_wave(self, projects, read_as_json, spreadsheet_path, column_mapping, columns_to_use):
        projects.return_value = self.projects_api.get_all_projects()
        spreadsheet_path.return_value = "test.xls"
        column_mapping.return_value = {
            "Wave name": "Wave name",
            "Wave date": "Wave date",
            "Source Url": "Source Url"
        }
        columns_to_use.return_value = ["Wave name", "Wave date", "Source Url"]
        read_as_json.return_value = [
            {
                "Wave name": "Wave1",
                "not needed": "asdflkasjdf",
                "not needed_2": 123,
                "Wave date": 1609459200000,
                "notneeded3": -1,
                "notneeded4": "qqq",
                "Source Url": "http://example.com/diaspora/diaspora-client.git"
            },
            {
                "Wave name": "Wave1",
                "not needed": "asdflkasjdf",
                "not needed_2": 124,
                "Wave date": 1609459200000,
                "notneeded3": 0,
                "notneeded4": "qqq",
                "Source Url": "http://example.com/brightbox/puppet.git"
            }
        ]
        expected = ["4", "80"]
        actual = self.wcli.get_ids_to_stage_wave("Wave1")
        self.assertListEqual(expected, actual)

    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_columns', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_column_mapping', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_path', new_callable=mock.PropertyMock)
    @mock.patch.object(WaveSpreadsheetHandler, "read_file_as_json")
    @mock.patch.object(BaseStageClass, "open_projects_file")
    def test_get_ids_to_stage_wave_no_waves(self, projects, read_as_json, spreadsheet_path, column_mapping, columns_to_use):
        projects.return_value = self.projects_api.get_all_projects()
        spreadsheet_path.return_value = "test.xls"
        column_mapping.return_value = {
            "Wave name": "Wave name",
            "Wave date": "Wave date",
            "Source Url": "Source Url"
        }
        columns_to_use.return_value = ["Wave name", "Wave date", "Source Url"]
        read_as_json.return_value = []
        expected = []
        actual = self.wcli.get_ids_to_stage_wave("Wave1")
        self.assertListEqual(expected, actual)
