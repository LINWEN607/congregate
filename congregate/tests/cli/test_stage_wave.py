import unittest
from unittest import mock
from pytest import mark
from congregate.cli.stage_wave import WaveStageCLI
from congregate.cli.stage_base import BaseStageClass
from congregate.migration.meta.etl import WaveSpreadsheetHandler
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.users import MockUsersApi


@mark.unit_test
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
    @mock.patch('congregate.helpers.conf.Config.source_type', new_callable=mock.PropertyMock)
    @mock.patch.object(WaveSpreadsheetHandler, "read_file_as_json")
    @mock.patch.object(BaseStageClass, "open_projects_file")
    def test_stage_wave(self, projects, read_as_json, mock_source_type, spreadsheet_path, column_mapping, columns_to_use, mock_groups, mock_users):
        mock_source_type.return_value = "gitlab"
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
                "jobs_enabled": None,
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
                'http_url_to_repo': 'http://example.com/diaspora/diaspora-client.git',
                'shared_runners_enabled': True,
                'archived': False,
                'shared_with_groups': [],
                'default_branch': 'master'
            },
            {
                "id": 80,
                "name": "Puppet",
                "namespace": "brightbox",
                "path": "puppet",
                "path_with_namespace": "brightbox/puppet",
                "visibility": "private",
                "description": None,
                "jobs_enabled": None,
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
                'http_url_to_repo': 'http://example.com/brightbox/puppet.git',
                'shared_runners_enabled': True,
                'archived': False,
                'shared_with_groups': [],
                'default_branch': 'master'
            }
        ]

        self.wcli.stage_wave("Wave1")
        actual = self.wcli.staged_projects

        self.assertEqual(len(expected), len(actual))
        for i in range(len(expected)):
            self.assertEqual(
                expected[i].items(), actual[i].items())

    @mock.patch.object(WaveStageCLI, 'open_users_file')
    @mock.patch.object(WaveStageCLI, 'open_groups_file')
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_columns', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_column_mapping', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_path', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.source_type', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.source_host', new_callable=mock.PropertyMock)
    @mock.patch.object(WaveSpreadsheetHandler, "read_file_as_json")
    @mock.patch.object(BaseStageClass, "open_projects_file")
    def test_stage_wave_mixed_project(self, projects, read_as_json, mock_source_host, mock_source_type, spreadsheet_path, column_mapping, columns_to_use, mock_groups, mock_users):
        mock_source_type.return_value = "gitlab"
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
        projects.return_value = self.projects_api.get_all_projects()
        mock_source_host.return_value = "http://example.com/"
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
                "Source Url": "http://example.com/brightbox/puppet"
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
                "jobs_enabled": None,
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
                'http_url_to_repo': 'http://example.com/diaspora/diaspora-client.git',
                'shared_runners_enabled': True,
                'archived': False,
                'shared_with_groups': [],
                'default_branch': 'master'
            },
            {
                "id": 80,
                "name": "Puppet",
                "namespace": "brightbox",
                "path": "puppet",
                "path_with_namespace": "brightbox/puppet",
                "visibility": "private",
                "description": None,
                "jobs_enabled": None,
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
                'http_url_to_repo': 'http://example.com/brightbox/puppet.git',
                'shared_runners_enabled': True,
                'archived': False,
                'shared_with_groups': [],
                'default_branch': 'master'
            }
        ]

        self.wcli.stage_wave("Wave1")
        actual = self.wcli.staged_projects

        self.assertEqual(len(expected), len(actual))
        for i in range(len(expected)):
            self.assertEqual(
                expected[i].items(), actual[i].items())

    @mock.patch.object(WaveStageCLI, 'open_users_file')
    @mock.patch.object(WaveStageCLI, 'open_groups_file')
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_columns', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_column_mapping', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_path', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.source_type', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.source_host', new_callable=mock.PropertyMock)
    @mock.patch.object(WaveSpreadsheetHandler, "read_file_as_json")
    @mock.patch.object(BaseStageClass, "open_projects_file")
    def test_stage_wave_mixed_project_and_group(self, projects, read_as_json, mock_source_host, mock_source_type, spreadsheet_path, column_mapping, columns_to_use, mock_groups, mock_users):
        mock_source_type.return_value = "gitlab"
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
        projects.return_value = self.projects_api.get_all_projects()
        mock_source_host.return_value = "http://example.com/"
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
                "Source Url": "http://example.com/foo-bar-3"
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
                "jobs_enabled": None,
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
                'http_url_to_repo': 'http://example.com/diaspora/diaspora-client.git',
                'shared_runners_enabled': True,
                'archived': False,
                'shared_with_groups': [],
                'default_branch': 'master'
            },
            {
                "id": 6,
                "name": "Puppet",
                "namespace": "brightbox",
                "path": "puppet",
                "path_with_namespace": "brightbox/puppet",
                "visibility": "private",
                "description": None,
                "jobs_enabled": None,
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
                'http_url_to_repo': 'http://example.com/brightbox/puppet.git',
                'shared_runners_enabled': True,
                'archived': False,
                'shared_with_groups': [],
                'default_branch': 'master'
            }
        ]

        self.wcli.stage_wave("Wave1")
        actual = self.wcli.staged_projects

        self.assertEqual(len(expected), len(actual))
        for i in range(len(expected)):
            self.assertEqual(
                expected[i].items(), actual[i].items())

    @mock.patch.object(WaveStageCLI, 'get_parent_id')
    @mock.patch.object(WaveStageCLI, 'open_users_file')
    @mock.patch.object(WaveStageCLI, 'open_groups_file')
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_columns', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_column_mapping', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.wave_spreadsheet_path', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.source_type', new_callable=mock.PropertyMock)
    @mock.patch.object(WaveSpreadsheetHandler, "read_file_as_json")
    @mock.patch.object(BaseStageClass, "open_projects_file")
    def test_stage_wave_with_parent_group(self, projects, read_as_json, mock_source_type, spreadsheet_path, column_mapping, columns_to_use, mock_groups, mock_users, mock_parent_id):
        mock_source_type.return_value = "gitlab"
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
        projects.return_value = self.projects_api.get_all_projects()
        spreadsheet_path.return_value = "test.xls"
        column_mapping.return_value = {
            "Wave name": "Wave name",
            "Wave date": "Wave date",
            "Source Url": "Source Url",
            "Parent Path": "Group",
            "swc_manager_name": "SWC Manager Name",
            "swc_manager_email": "SWC Manager Email",
            "swc_id": "SWC AA ID"
        }
        columns_to_use.return_value = [
            "Wave name", "Wave date", "Source Url", "Group", "SWC Manager Name", "SWC Manager Email", "SWC AA ID"]

        mock_parent_id.side_effect = [None, None]

        read_as_json.return_value = [
            {
                "Wave name": "Wave1",
                "not needed": "asdflkasjdf",
                "not needed_2": 123,
                "Wave date": 1609459200000,
                "Group": "/path/to/group",
                "notneeded3": -1,
                "notneeded4": "qqq",
                "Source Url": "http://example.com/diaspora/diaspora-client.git",
                "SWC Manager Name": "application owner name",
                "SWC Manager Email": "owner@example.com",
                "SWC AA ID": "application group"
            },
            {
                "Wave name": "Wave1",
                "not needed": "asdflkasjdf",
                "not needed_2": 124,
                "Wave date": 1609459200000,
                "Group": "/path/to/group",
                "notneeded3": 0,
                "notneeded4": "qqq",
                "Source Url": "http://example.com/brightbox/puppet.git",
                "SWC Manager Name": "application owner name",
                "SWC Manager Email": "owner@example.com",
                "SWC AA ID": "application group"
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
                "jobs_enabled": None,
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
                'http_url_to_repo': 'http://example.com/diaspora/diaspora-client.git',
                'shared_runners_enabled': True,
                'archived': False,
                'shared_with_groups': [],
                'default_branch': 'master',
                'target_namespace': 'path/to/group',
                "swc_manager_name": "application owner name",
                "swc_manager_email": "owner@example.com",
                "swc_id": "application group"
            },
            {
                "id": 80,
                "name": "Puppet",
                "namespace": "brightbox",
                "path": "puppet",
                "path_with_namespace": "brightbox/puppet",
                "visibility": "private",
                "description": None,
                "jobs_enabled": None,
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
                'http_url_to_repo': 'http://example.com/brightbox/puppet.git',
                'shared_runners_enabled': True,
                'archived': False,
                'shared_with_groups': [],
                'default_branch': 'master',
                'target_namespace': 'path/to/group',
                "swc_manager_name": "application owner name",
                "swc_manager_email": "owner@example.com",
                "swc_id": "application group"
            }
        ]

        self.wcli.stage_wave("Wave1")
        actual = self.wcli.staged_projects

        self.assertEqual(len(expected), len(actual))
        for i in range(len(expected)):
            self.assertEqual(
                expected[i].items(), actual[i].items())

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

    @mock.patch('congregate.helpers.conf.Config.source_host', new_callable=mock.PropertyMock)
    def test_sanitize_project_path(self, mock_host):
        mock_host.return_value = "http://gitlab.com"
        url = "http://gitlab.com/path/to/repo.git"

        expected = "path/to/repo.git"
        actual = self.wcli.sanitize_project_path(url)

        self.assertEqual(expected, actual)

    @mock.patch('congregate.helpers.conf.Config.source_host', new_callable=mock.PropertyMock)
    def test_sanitize_project_path_with_spaces(self, mock_host):
        mock_host.return_value = "http://gitlab.com"
        url = "http://gitlab.com/path/to/repo.git    "

        expected = "path/to/repo.git"
        actual = self.wcli.sanitize_project_path(url)

        self.assertEqual(expected, actual)

    def test_find_group(self):
        self.wcli.group_paths = {
            "test-group": {
                "path": "test-group"
            }
        }
        expected = {
            "path": "test-group"
        }
        actual = self.wcli.find_group("http://github.test.com/test-group")

        self.assertEqual(expected, actual)
    
    def test_find_group_invalid(self):
        self.wcli.group_paths = {
            "test-group": {
                "path": "test-group"
            }
        }
        actual = self.wcli.find_group("http://github.test.com/test-group/test-group")

        self.assertIsNone(actual)