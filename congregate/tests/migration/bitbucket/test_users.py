import unittest
from mock import patch, PropertyMock

from congregate.tests.mockapi.bitbucket.users import MockUsersApi
from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket.users import UsersClient


class UserTests(unittest.TestCase):
    def setUp(self):
        self.mock_users = MockUsersApi()
        self.users = UsersClient()

    @patch('__builtin__.raw_input')
    @patch.object(UsersApi, "get_all_users")
    @patch('congregate.helpers.conf.Config.external_source_url', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.external_user_token', new_callable=PropertyMock)
    def test_retrieve_user_info(self, mock_ext_src_url, mock_ext_user_token, mock_get_all_users, mock_open):
        mock_ext_src_url.return_value = "http://localhost:7990"
        mock_ext_user_token.return_value = "username:password"
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
        self.assertEqual(sorted(self.users.retrieve_user_info()),
                         sorted(expected_users))
