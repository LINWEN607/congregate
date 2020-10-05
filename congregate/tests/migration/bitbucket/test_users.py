import unittest
import pytest
from mock import patch, PropertyMock

from congregate.tests.mockapi.bitbucket.users import MockUsersApi
from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket.users import UsersClient
from congregate.helpers.misc_utils import json_pretty


@pytest.mark.unit_test
class UsersTests(unittest.TestCase):
    def setUp(self):
        self.mock_users = MockUsersApi()
        self.maxDiff = None

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(UsersApi, "get_all_users")
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_retrieve_user_info(self, mock_ext_src_url, mock_ext_user_token, mock_get_all_users, mock_open, mock_file):
        users = UsersClient()
        mock_ext_src_url.return_value = "http://localhost:7990"
        mock_ext_user_token.return_value = "username:password"
        mock_get_all_users.return_value = self.mock_users.get_all_users()
        mock_open.return_value = mock_file
        expected_users = [
            {
                "username": "user1",
                "email": "user1@example.com",
                "id": 2,
                "name": "user1",
                "state": "active"
            },
            {
                "username": "user2",
                "email": "user2@example.com",
                "id": 3,
                "name": "user2",
                "state": "active"
            }
        ]
        self.assertEqual(users.retrieve_user_info().sort(
            key=lambda x: x["id"]), expected_users.sort(key=lambda x: x["id"]))

    
    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(UsersApi, "get_all_users")
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.users_to_ignore', new_callable=PropertyMock)
    def test_retrieve_user_info_ignore_user(self, mock_users_to_ignore, mock_ext_src_url, mock_ext_user_token, mock_get_all_users, mock_open, mock_file):
        mock_ext_src_url.return_value = "http://localhost:7990"
        mock_ext_user_token.return_value = "username:password"
        mock_get_all_users.return_value = self.mock_users.get_all_users()
        mock_open.return_value = mock_file
        mock_users_to_ignore.return_value = ["user1"]
        users = UsersClient()
        expected_users = [
            {
                "username": "user2",
                "email": "user2@example.com",
                "id": 3,
                "name": "user2",
                "state": "active"
            }
        ]
        actual_users = users.retrieve_user_info()
        for i, _ in enumerate(actual_users):
            self.assertDictEqual(expected_users[i], actual_users[i])