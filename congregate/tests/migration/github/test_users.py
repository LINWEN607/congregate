import unittest
import pytest
from mock import patch, PropertyMock, MagicMock
import warnings
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock

from congregate.helpers.misc_utils import json_pretty
from congregate.helpers.mdbc import MongoConnector
from congregate.tests.mockapi.github.users import MockUsersApi
from congregate.migration.github.users import UsersClient
from congregate.migration.github.api.users import UsersApi


@pytest.mark.unit_test
class UsersTests(unittest.TestCase):
    def setUp(self):
        self.mock_users = MockUsersApi()
        self.users = self.mock_user_client()

    def tearDown(self):
        self.users.connect_to_mongo().drop_collection("projects")
        self.users.connect_to_mongo().drop_collection("groups")
        self.users.connect_to_mongo().drop_collection("users")

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(UsersApi, "get_all_users")
    @patch.object(UsersApi, "get_user")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    @patch("congregate.helpers.conf.Config.source_token", new_callable=PropertyMock)
    def test_retrieve_user_info(self,
                                mock_source_token,
                                mock_source_host,
                                mock_single_user,
                                mock_users,
                                mock_open,
                                mock_file):
        with patch("congregate.migration.github.users.start_multi_process", new=self.mock_multi_process):
            mock_source_token.return_value = "token"
            mock_source_host.return_value = "https://github.com"
            mock_user1 = MagicMock()
            type(mock_user1).status_code = PropertyMock(return_value=200)
            mock_user1.json.return_value = self.mock_users.get_user()[0]
            mock_user2 = MagicMock()
            type(mock_user2).status_code = PropertyMock(return_value=200)
            mock_user2.json.return_value = self.mock_users.get_user()[1]
            mock_user3 = MagicMock()
            type(mock_user3).status_code = PropertyMock(return_value=200)
            mock_user3.json.return_value = self.mock_users.get_user()[2]
            mock_single_user.side_effect = [mock_user1, mock_user2, mock_user3]

            mock_users.return_value = self.mock_users.get_all_users()
            mock_open.return_value = mock_file

            self.users.retrieve_user_info()

            actual_users = [d for d, _ in self.users.connect_to_mongo().stream_collection("users")]
            
            expected_users = [
                {
                    "username": "ghost",
                    "name": None,
                    "id": 1,
                    "state": "active",
                    "avatar_url": "https://github.gitlab-proserv.net/avatars/u/1?",
                    "is_admin": False,
                    "email": None
                },
                {
                    "username": "github-enterprise",
                    "name": None,
                    "id": 2,
                    "state": "active",
                    "avatar_url": "https://github.gitlab-proserv.net/avatars/u/2?",
                    "is_admin": False,
                    "email": None
                },
                {
                    "username": "gitlab",
                    "name": None,
                    "id": 3,
                    "state": "active",
                    "avatar_url": "https://github.gitlab-proserv.net/avatars/u/3?",
                    "is_admin": True,
                    "email": None
                }
            ]

            self.assertGreater(len(actual_users), 0)

            for i, _ in enumerate(expected_users):
                self.assertDictEqual(expected_users[i], actual_users[i])

    @patch.object(UsersApi, "get_user")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    def test_format_users_with_permissions(self,
                                           mock_source_host,
                                           mock_single_user):
        mock_source_host.return_value = "https://github.com"

        mock_user1 = MagicMock()
        type(mock_user1).status_code = PropertyMock(return_value=200)
        mock_user1.json.return_value = self.mock_users.get_user()[0]
        mock_user2 = MagicMock()
        type(mock_user2).status_code = PropertyMock(return_value=200)
        mock_user2.json.return_value = self.mock_users.get_user()[1]
        mock_user3 = MagicMock()
        type(mock_user3).status_code = PropertyMock(return_value=200)
        mock_user3.json.return_value = self.mock_users.get_user()[2]
        mock_single_user.side_effect = [mock_user1, mock_user2, mock_user3]

        actual_users = self.users.format_users([
            {"login": "ghost", "permissions": 40},
            {"login": "github-enterprise", "permissions": 30},
            {"login": "gitlab", "permissions": 20}
        ])

        expected_users = [
            {
                "username": "ghost",
                "name": None,
                "id": 1,
                "state": "active",
                "avatar_url": "",
                "is_admin": False,
                "email": None,
                "access_level": 40
            },
            {
                "username": "github-enterprise",
                "name": None,
                "id": 2,
                "state": "active",
                "avatar_url": "",
                "is_admin": False,
                "email": None,
                "access_level": 30
            },
            {
                "username": "gitlab",
                "name": None,
                "id": 3,
                "state": "active",
                "avatar_url": "",
                "is_admin": True,
                "email": None,
                "access_level": 20
            }
        ]

        self.assertEqual(actual_users.sort(
            key=lambda x: x["id"]), expected_users.sort(key=lambda x: x["id"]))

    @patch.object(UsersApi, "get_user")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    def test_format_users_with_error(self,
                                     mock_source_host,
                                     mock_single_user):
        mock_source_host.return_value = "https://github.com"

        mock_user1 = MagicMock()
        type(mock_user1).status_code = PropertyMock(return_value=200)
        mock_user1.json.return_value = self.mock_users.get_user()[0]
        mock_user2 = MagicMock()
        type(mock_user2).status_code = PropertyMock(return_value=404)
        mock_user2.json.return_value = {
            "message": "Not Found",
            "documentation_url": "https://developer.github.com/enterprise/2.21/v3"
        }
        mock_user3 = MagicMock()
        type(mock_user3).status_code = PropertyMock(return_value=200)
        mock_user3.json.return_value = self.mock_users.get_user()[2]
        mock_single_user.side_effect = [mock_user1, mock_user2, mock_user3]

        actual_users = self.users.format_users([
            {"login": "ghost", "permissions": 40},
            {"login": "github-enterprise", "permissions": 30},
            {"login": "gitlab", "permissions": 20}
        ])

        expected_users = [
            {
                "username": "ghost",
                "name": None,
                "id": 1,
                "state": "active",
                "avatar_url": "",
                "is_admin": False,
                "email": None,
                "access_level": 40
            },
            {
                "username": "gitlab",
                "name": None,
                "id": 3,
                "state": "active",
                "avatar_url": "",
                "is_admin": True,
                "email": None,
                "access_level": 20
            }
        ]

        self.assertEqual(actual_users.sort(
            key=lambda x: x["id"]), expected_users.sort(key=lambda x: x["id"]))

    def mock_user_client(self):
        with patch.object(UsersClient, "connect_to_mongo") as mongo_mock:
            mongo_mock.return_value = MongoConnector(host="test-server", port=123456, client=mongomock.MongoClient)
            return UsersClient()

    def mock_multi_process(self, func, iterable):
        for data in iterable:
            func(data)