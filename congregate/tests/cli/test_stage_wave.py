import unittest
import mock
import json
import pytest
from congregate.cli.stage_wave import WaveStageCLI
from congregate.cli.stage_base import BaseStageClass
from congregate.migration.meta.etl import WaveSpreadsheetHandler
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.users import MockUsersApi


@pytest.mark.unit_test
class StageWaveTests(unittest.TestCase):
    def setUp(self):
        self.projects_api = MockProjectsApi()
        self.groups_api = MockGroupsApi()
        self.users_api = MockUsersApi()
        self.mock = mock.MagicMock()
        self.wcli = WaveStageCLI()

    @mock.patch.object(WaveStageCLI, 'open_users_file')
    @mock.patch.object(WaveStageCLI, 'open_groups_file')
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_columns', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_column_mapping', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_path', new_callable=mock.PropertyMock)
    @mock.patch.object(WaveSpreadsheetHandler, "read_file_as_json")
    @mock.patch.object(BaseStageClass, "open_projects_file")
    def test_stage_wave(self, projects, read_as_json, spreadsheet_path, column_mapping, columns_to_use, mock_groups, mock_users):
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
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
        expected = [
            {
                "id": 4,
                "name": "Diaspora Client",
                "namespace": "diaspora",
                "path": "diaspora-client",
                "path_with_namespace": "diaspora/diaspora-client",
                "visibility": "private",
                "description": "Project that does stuff",
                "project_type": "group",
                "members": [
                    {
                        "id": 2,
                        "username": "john_doe",
                        "name": "John Doe",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                        "expires_at": "2012-10-22T14:13:35Z",
                        "access_level": 30
                    }
                ]
            },
            {
                "id": 80,
                "name": "Puppet",
                "namespace": "brightbox",
                "path": "puppet",
                "path_with_namespace": "brightbox/puppet",
                "visibility": "private",
                "description": None,
                "project_type": "group",
                "members": [
                    {
                        "id": 2,
                        "username": "john_doe",
                        "name": "John Doe",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                        "expires_at": "2012-10-22T14:13:35Z",
                        "access_level": 30
                    }
                ]
            }
        ]
   
        self.wcli.stage_wave("Wave1")
        actual = self.wcli.staged_projects
        self.assertListEqual(expected, actual)

    @mock.patch.object(WaveStageCLI, 'open_users_file')
    @mock.patch.object(WaveStageCLI, 'open_groups_file')
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_columns', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_column_mapping', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_path', new_callable=mock.PropertyMock)
    @mock.patch.object(WaveSpreadsheetHandler, "read_file_as_json")
    @mock.patch.object(BaseStageClass, "open_projects_file")
    def test_stage_wave_with_parent_group(self, projects, read_as_json, spreadsheet_path, column_mapping, columns_to_use, mock_groups, mock_users):
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
        projects.return_value = self.projects_api.get_all_projects()
        spreadsheet_path.return_value = "test.xls"
        column_mapping.return_value = {
            "Wave name": "Wave name",
            "Wave date": "Wave date",
            "Source Url": "Source Url",
            "Parent Path": "Group"
        }
        columns_to_use.return_value = ["Wave name", "Wave date", "Source Url", "Group"]
        read_as_json.return_value = [
            {
                "Wave name": "Wave1",
                "not needed": "asdflkasjdf",
                "not needed_2": 123,
                "Wave date": 1609459200000,
                "Group": "/path/to/group",
                "notneeded3": -1,
                "notneeded4": "qqq",
                "Source Url": "http://example.com/diaspora/diaspora-client.git"
            },
            {
                "Wave name": "Wave1",
                "not needed": "asdflkasjdf",
                "not needed_2": 124,
                "Wave date": 1609459200000,
                "Group": "/path/to/group",
                "notneeded3": 0,
                "notneeded4": "qqq",
                "Source Url": "http://example.com/brightbox/puppet.git"
            }
        ]
        expected = [
            {
                "id": 4,
                "name": "Diaspora Client",
                "namespace": "diaspora",
                "path": "diaspora-client",
                "path_with_namespace": "diaspora/diaspora-client",
                "visibility": "private",
                "description": "Project that does stuff",
                "project_type": "group",
                "members": [
                    {
                        "id": 2,
                        "username": "john_doe",
                        "name": "John Doe",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                        "expires_at": "2012-10-22T14:13:35Z",
                        "access_level": 30
                    }
                ],
                "target_namespace": "/path/to/group"
            },
            {
                "id": 80,
                "name": "Puppet",
                "namespace": "brightbox",
                "path": "puppet",
                "path_with_namespace": "brightbox/puppet",
                "visibility": "private",
                "description": None,
                "project_type": "group",
                "members": [
                    {
                        "id": 2,
                        "username": "john_doe",
                        "name": "John Doe",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                        "expires_at": "2012-10-22T14:13:35Z",
                        "access_level": 30
                    }
                ],
                "target_namespace": "/path/to/group"
            }
        ]
   
        self.wcli.stage_wave("Wave1")
        actual = self.wcli.staged_projects
        self.assertListEqual(expected, actual)

    @mock.patch.object(WaveStageCLI, 'open_users_file')
    @mock.patch.object(WaveStageCLI, 'open_groups_file')
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_columns', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_column_mapping', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_path', new_callable=mock.PropertyMock)
    @mock.patch.object(WaveSpreadsheetHandler, "read_file_as_json")
    @mock.patch.object(BaseStageClass, "open_projects_file")
    def test_get_ids_to_stage_wave_no_waves(self, projects, read_as_json, spreadsheet_path, column_mapping, columns_to_use, mock_groups, mock_users):
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
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
        self.wcli.stage_wave("Wave1")
        actual = self.wcli.staged_projects
        self.assertListEqual(expected, actual)
