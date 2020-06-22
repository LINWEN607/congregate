import unittest
from mock import patch

from congregate.tests.mockapi.bitbucket.users import MockUsersApi
from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket.users import UsersClient


class UserTests(unittest.TestCase):
    def setUp(self):
        self.mock_users = MockUsersApi()
        self.users = UsersClient()

    @patch('__builtin__.raw_input')
    @patch.object(UsersApi, "get_all_users")
    def test_retrieve_user_info(self, mock_get_all_users, mock_open):
        mock_get_all_users.return_value = self.mock_users.get_all_users()
        mock_open.return_value = []
        expected_users = [
            {
                "username": "user1",
                "email": "user1@example.com",
                "id": 2,
                "name": "user1",
                "web_url": "http://localhost:7990/users/user1",
                "state": "active"
            },
            {
                "username": "user2",
                "email": "user2@example.com",
                "id": 3,
                "name": "user2",
                "web_url": "http://localhost:7990/users/user2",
                "state": "active"
            }
        ]
        self.assertEqual(sorted(self.users.retrieve_user_info(
            "host", "token")), sorted(expected_users))
