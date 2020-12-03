import unittest
import pytest
from mock import patch, PropertyMock

from congregate.tests.mockapi.bitbucket.groups import MockGroupsApi
from congregate.migration.bitbucket.groups import GroupsClient
from congregate.migration.bitbucket.api.groups import GroupsApi


@pytest.mark.unit_test
class GroupsTests(unittest.TestCase):
    def setUp(self):
        self.mock_groups = MockGroupsApi()
        self.groups = GroupsClient()

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(GroupsApi, "get_all_groups")
    @patch.object(GroupsApi, "get_all_group_users")
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_retrieve_group_info(self, mock_ext_user_token, mock_ext_src_url, mock_get_all_group_users, mock_get_all_groups, mock_open, mock_file):
        mock_ext_src_url.return_value = "http://localhost:7990"
        mock_ext_user_token.return_value = "username:password"
        mock_get_all_group_users.return_value = self.mock_groups.get_all_group_members()
        mock_get_all_groups.return_value = self.mock_groups.get_all_groups()
        mock_open.return_value = mock_file
        expected = {
            "test-group": self.mock_groups.get_all_group_members()
        }
        actual = self.groups.retrieve_group_info()
        self.assertDictEqual(expected, actual)