import unittest
from unittest.mock import patch, PropertyMock
from pytest import mark

from congregate.tests.mockapi.bitbucket.groups import MockGroupsApi
from congregate.migration.bitbucket.groups import GroupsClient
from congregate.migration.bitbucket.api.groups import GroupsApi


@mark.unit_test
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
    @patch('congregate.helpers.conf.Config.users_to_ignore', new_callable=PropertyMock)
    def test_retrieve_group_info(self, mock_users_to_ignore, mock_ext_user_token, mock_ext_src_url, mock_get_all_group_users, mock_get_all_groups, mock_open, mock_file):
        mock_users_to_ignore.return_value = ["admin"]
        mock_ext_src_url.return_value = "http://localhost:7990"
        mock_ext_user_token.return_value = "username:password"
        mock_get_all_group_users.return_value = self.mock_groups.get_all_group_members()
        mock_get_all_groups.return_value = self.mock_groups.get_all_groups()
        mock_open.return_value = mock_file
        expected = {
            "test-group": {
                "users": [
                    {
                        "id": 2,
                        "username": "user1",
                        "name": "user1",
                        "email": "user1@example.com",
                        "state": "active"
                    },
                    {
                        "id": 3,
                        "username": "user2",
                        "name": "user2",
                        "email": "user2@example.com",
                        "state": "active"
                    },
                    {
                        "id": 4,
                        "username": "user3",
                        "name": "user3",
                        "email": "user3@example.com",
                        "state": "active"
                    },
                    {
                        "id": 5,
                        "username": "user4",
                        "name": "user4",
                        "email": "user4@example.com",
                        "state": "active"
                    },
                    {
                        "id": 6,
                        "username": "user5",
                        "name": "user5",
                        "email": "user5@example.com",
                        "state": "active"
                    }
                ],
                "repos": [],
                "projects": []
            }
        }
        actual = self.groups.retrieve_group_info()
        print(actual)
        self.assertDictEqual(expected, actual)
