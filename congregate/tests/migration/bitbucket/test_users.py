import unittest
import warnings
from unittest.mock import patch, PropertyMock
from pytest import mark
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock

from congregate.helpers.mdbc import MongoConnector
from congregate.tests.mockapi.bitbucket.users import MockUsersApi
from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket.users import UsersClient
from gitlab_ps_utils.json_utils import json_pretty


@mark.unit_test
class UsersTests(unittest.TestCase):
    def setUp(self):
        self.mock_users = MockUsersApi()

    @patch.object(MongoConnector, "close_connection")
    @patch.object(UsersApi, "get_all_users")
    @patch('congregate.helpers.conf.Config.source_token',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
           new_callable=PropertyMock)
    def test_retrieve_user_info(
            self, mock_ext_src_url, mock_ext_user_token, mock_get_all_users, mock_close_connection):
        users = UsersClient()
        mock_ext_src_url.return_value = "http://bitbucket.company.com"
        mock_ext_user_token.return_value = "username:password"
        mock_get_all_users.return_value = self.mock_users.get_all_users()
        mock_close_connection.return_value = None
        expected_users = [
            {
                "username": "admin",
                "email": "sysadmin@yourcompany.com",
                "id": 1,
                "name": "John Doe",
                "state": "active"
            },
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

        mongo = MongoConnector(client=mongomock.MongoClient)

        for user in self.mock_users.get_all_users():
            users.handle_retrieving_users(user, mongo=mongo)
        actual_users = [d for d, _ in mongo.stream_collection(
            "users-bitbucket.company.com")]

        self.assertEqual(len(actual_users), len(expected_users))

        for i, _ in enumerate(expected_users):
            self.assertDictEqual(expected_users[i], actual_users[i])

    @patch.object(MongoConnector, "close_connection")
    @patch.object(UsersApi, "get_all_users")
    @patch('congregate.helpers.conf.Config.source_token',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.users_to_ignore',
           new_callable=PropertyMock)
    def test_retrieve_user_info_ignore_user(
            self, mock_users_to_ignore, mock_ext_src_url, mock_ext_user_token, mock_get_all_users, mock_close_connection):
        mock_ext_src_url.return_value = "http://bitbucket.company.com"
        mock_ext_user_token.return_value = "username:password"
        mock_get_all_users.return_value = self.mock_users.get_all_users()
        mock_close_connection.return_value = None
        mock_users_to_ignore.return_value = ["user1"]
        users = UsersClient()
        expected_users = [
            {
                "username": "admin",
                "email": "sysadmin@yourcompany.com",
                "id": 1,
                "name": "John Doe",
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

        mongo = MongoConnector(client=mongomock.MongoClient)

        for user in self.mock_users.get_all_users():
            users.handle_retrieving_users(user, mongo=mongo)
        actual_users = [d for d, _ in mongo.stream_collection(
            "users-bitbucket.company.com")]

        self.assertEqual(len(actual_users), len(expected_users))

        for i, _ in enumerate(expected_users):
            self.assertDictEqual(expected_users[i], actual_users[i])

    @patch('congregate.helpers.conf.Config.users_to_ignore', new_callable=PropertyMock)
    def test_is_user_needed_ignored_false(self, mock_ignore):
        mock_ignore.return_value = ['user1']
        users = UsersClient()
        user = {
            "id": 2,
            "slug": "user1"
        }
        self.assertFalse(users.is_user_needed(user))

    @patch('congregate.helpers.conf.Config.users_to_ignore', new_callable=PropertyMock)
    def test_is_user_needed_ignored_true(self, mock_ignore):
        mock_ignore.return_value = ['user1']
        users = UsersClient()
        user = {
            "id": 2,
            "slug": "user2"
        }
        self.assertTrue(users.is_user_needed(user))
