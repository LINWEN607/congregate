import unittest
from unittest import mock
from pytest import mark
from congregate.cli.stage_wave_csv_generator import WaveStageCSVGeneratorCLI
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.users import MockUsersApi


@mark.unit_test
class StageWaveCSVGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.projects_api = MockProjectsApi()
        self.groups_api = MockGroupsApi()
        self.users_api = MockUsersApi()
        self.mock = mock.MagicMock()
        self.wcli = None

    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_path', new_callable=mock.PropertyMock)
    @mock.patch.object(WaveStageCSVGeneratorCLI, "open_projects_file")
    def test_bad_map_logs_error_and_returns(self, projects, spreadsheet_path):
        projects.return_value = self.projects_api.get_all_projects()
        self.wcli = WaveStageCSVGeneratorCLI()
        spreadsheet_path.return_value = "test.xls"
        header_info = {
            "headers": ["Wave name", "Wave date", "Source Url", "Parent Path"],
            "header_map": {
                "Source Url": "some_prop_doesnt_exist"
            }
        }

        with self.assertLogs(self.wcli.log.name) as cm:
            self.wcli.generate(
                destination_file="templates/generate_test.csv",
                header_info=header_info,
                dry_run=False
            )

        self.assertEqual(cm.output, [
            "INFO:congregate.helpers.base_class:Generating wave file with header information: {'headers': ['Wave name', 'Wave date', 'Source Url', 'Parent Path'], 'header_map': {'Source Url': 'some_prop_doesnt_exist'}}",
            "ERROR:congregate.helpers.base_class:Property some_prop_doesnt_exist does not exist on projects. Header map is {'Source Url': 'some_prop_doesnt_exist'}"
        ]
        )

        self.assertListEqual([], self.wcli.rows)

    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_columns', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_column_mapping', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_path', new_callable=mock.PropertyMock)
    @mock.patch.object(WaveStageCSVGeneratorCLI, "open_projects_file")
    def test_generate_happy(self, projects, spreadsheet_path, column_mapping, columns_to_use):
        projects.return_value = self.projects_api.get_all_projects()
        self.wcli = WaveStageCSVGeneratorCLI()
        spreadsheet_path.return_value = "test.xls"
        column_mapping.return_value = {
            "Source Url": "Source Url",
        }
        columns_to_use.return_value = [
            "Wave name", "Wave date", "Source Url", "Parent Path"]
        # We will check against the objects stored [[row],[row]] entity
        expected = [
            ["Wave name", "Wave date", "Source Url", "Parent Path"],
            ["", "", "http://example.com/diaspora/diaspora-client.git", ""],
            ["", "", "http://example.com/brightbox/puppet.git", ""],
            # Odd our project mock returns two of same project?
            ["", "", "http://example.com/brightbox/puppet.git", ""]
        ]
        header_info = {
            "headers": ["Wave name", "Wave date", "Source Url", "Parent Path"],
            "header_map": {
                "Source Url": "http_url_to_repo"
            }
        }
        self.wcli.generate(destination_file="templates/generate_test.csv",
                           header_info=header_info, dry_run=False)

        actual = self.wcli.rows

        self.assertEqual(len(expected), len(actual))
        for i, e in enumerate(expected):
            self.assertEqual(
                e, actual[i])
