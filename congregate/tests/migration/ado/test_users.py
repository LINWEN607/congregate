import unittest
import warnings
from unittest.mock import patch, PropertyMock
from pytest import mark
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock

from congregate.helpers.congregate_mdbc import CongregateMongoConnector
from congregate.tests.mockapi.ado.users import MockUsersApi
from congregate.migration.ado.api.users import UsersApi
from congregate.migration.ado.users import UsersClient


@mark.unit_test
class UsersTests(unittest.TestCase):
    def setUp(self):
        self.mock_users = MockUsersApi()

    @patch.object(CongregateMongoConnector, "close_connection")
    @patch.object(UsersApi, "get_all_users")
    @patch('congregate.helpers.conf.Config.source_token',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
           new_callable=PropertyMock)
    def test_retrieve_user_info(
            self, mock_ext_src_url, mock_ext_user_token, mock_get_all_users, mock_close_connection):
        users = UsersClient()
        mock_ext_src_url.return_value = "https://dev.azure.com/gitlab-ps"
        mock_ext_user_token.return_value = "username:password"
        mock_get_all_users.return_value = self.mock_users.get_all_users()
        mock_close_connection.return_value = None
        expected_users = [
            {
                "email": "john.doe@gitlabpsoutlook.onmicrosoft.com",
                "id": "aad.ZTlkMzM1NjgtZTZmMi03ZGVhLWI4ZmQtMzA4MzlmYjA2ODhm",
                "name": "John Doe",
                "state": "active",
                "username": "john.doe"
            },{
                "email": "paul.van.windmill@gitlabpsoutlook.onmicrosoft.com",
                "id": "aad.OTcwYTMwODktNTZjMC03ZmRiLWI1MDItYzIwZWVjM2Y1ZTM4",
                "name": "Paul van Windmill",
                "state": "active",
                "username": "paul.van.windmill"
            },{
                "email": "adam.bijman@gitlabpsoutlook.onmicrosoft.com",
                "id": "aad.NmEwOTg0ZWItYjI4Yy03YjVjLWJjZWItZTMwOTU3ZWQ2YTg4",
                "name": "Adam Bijman",
                "state": "active",
                "username": "adam.bijman"
            }
        ]

        mongo = CongregateMongoConnector(client=mongomock.MongoClient)

        for user in self.mock_users.get_all_users():
            users.handle_retrieving_user(user, mongo=mongo)
        actual_users = [d for d, _ in mongo.stream_collection(
            "users-dev.azure.com")]

        self.assertEqual(len(actual_users), len(expected_users))

        for i, _ in enumerate(expected_users):
            self.assertDictEqual(expected_users[i], actual_users[i])
