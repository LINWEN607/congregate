import unittest
from mock import patch, PropertyMock

from congregate.tests.mockapi.github.users import MockUsersApi
from congregate.migration.github.users import UsersClient
from congregate.migration.github.api.users import UsersApi


class UsersTests(unittest.TestCase):
    def setUp(self):
        self.mock_users = MockUsersApi()
        self.users = UsersClient()

    @patch("__builtin__.file")
    @patch("__builtin__.open")
    @patch.object(UsersApi, "get_all_users")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    @patch("congregate.helpers.conf.Config.source_token", new_callable=PropertyMock)
    def test_retrieve_org_info(self,
                               mock_source_token,
                               mock_source_host,
                               mock_users,
                               mock_open,
                               mock_file):

        mock_source_token.return_value = "token"
        mock_source_host.return_value = "https://github.com"
        mock_users.return_value = self.mock_users.get_all_users()
        mock_open.return_value = mock_file

        expected_users = [
            {
                "username": "ghost", 
                "state": "active", 
                "id": 1
            }, 
            {
                "username": "github-enterprise", 
                "state": "active", 
                "id": 2
            }, 
            {
                "username": "gitlab", 
                "state": "active", 
                "id": 3
            }
        ]

        self.assertEqual(sorted(self.users.retrieve_user_info()),
                         sorted(expected_users))
