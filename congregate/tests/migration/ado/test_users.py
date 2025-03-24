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

    @patch.object(CongregateMongoConnector, "close_connection")
    @patch.object(UsersApi, "get_user")
    @patch('congregate.helpers.conf.Config.source_token',
            new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
            new_callable=PropertyMock)
    def test_create_valid_username_and_name_from_cyrillic(
            self, mock_ext_src_url, mock_ext_user_token, mock_get_user, mock_close_connection):
        users = UsersClient()
        mock_ext_src_url.return_value = "https://dev.azure.com/gitlab-ps"
        mock_ext_user_token.return_value = "username:password"
        mock_close_connection.return_value = None

        user_data = {
            "subjectKind": "user",
            "directoryAlias": "fiodor.dostoevskii",
            "domain": "7cfe4c9f-829b-4857-89f9-dfa21e53e1d9",
            "principalName": "fiodor.dostoevskii@gitlabpsoutlook.onmicrosoft.com",
            "mailAddress": "fiodor.dostoevskii@gitlabpsoutlook.onmicrosoft.com",
            "origin": "aad",
            "originId": "29a04fc4-2ffc-4b07-83c6-fbcfeaa3db6d",
            "displayName": "Фёдор Достоевский",
            "_links": {
                "self": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.NzA4NjgxNWMtNDQ4NS03Y2NmLWE2NGUtNDczNTBjZTU3OGU1"
                },
                "memberships": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Memberships/aad.NzA4NjgxNWMtNDQ4NS03Y2NmLWE2NGUtNDczNTBjZTU3OGU1"
                },
                "membershipState": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/MembershipStates/aad.NzA4NjgxNWMtNDQ4NS03Y2NmLWE2NGUtNDczNTBjZTU3OGU1"
                },
                "storageKey": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/StorageKeys/aad.NzA4NjgxNWMtNDQ4NS03Y2NmLWE2NGUtNDczNTBjZTU3OGU1"
                },
                "avatar": {
                    "href": "https://dev.azure.com/gitlab-ps/_apis/GraphProfile/MemberAvatars/aad.NzA4NjgxNWMtNDQ4NS03Y2NmLWE2NGUtNDczNTBjZTU3OGU1"
                }
            },
            "url": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.NzA4NjgxNWMtNDQ4NS03Y2NmLWE2NGUtNDczNTBjZTU3OGU1",
            "descriptor": "aad.NzA4NjgxNWMtNDQ4NS03Y2NmLWE2NGUtNDczNTBjZTU3OGU1"
        }

        mock_get_user.return_value = user_data

        mongo = CongregateMongoConnector(client=mongomock.MongoClient)
        users.handle_retrieving_user(user_data, mongo=mongo)

        actual_users = [d for d, _ in mongo.stream_collection(
            "users-dev.azure.com")]

        self.assertEqual(len(actual_users), 1)
        self.assertEqual(actual_users[0]["username"], "fiodor.dostoevskii")
        self.assertEqual(actual_users[0]["name"], "Fiodor Dostoevskii")

    @patch.object(CongregateMongoConnector, "close_connection")
    @patch.object(UsersApi, "get_user")
    @patch('congregate.helpers.conf.Config.source_token',
            new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
            new_callable=PropertyMock)
    def test_create_valid_username_and_name_from_czech(
        self, mock_ext_src_url, mock_ext_user_token, mock_get_user, mock_close_connection):
        users = UsersClient()
        mock_ext_src_url.return_value = "https://dev.azure.com/gitlab-ps"
        mock_ext_user_token.return_value = "username:password"
        mock_close_connection.return_value = None

        user_data = {
            "subjectKind": "user",
            "directoryAlias": "Frantisek.Kupka",
            "domain": "7cfe4c9f-829b-4857-89f9-dfa21e53e1d9",
            "principalName": "Frantisek.Kupka@gitlabpsoutlook.onmicrosoft.com",
            "mailAddress": "Frantisek.Kupka@gitlabpsoutlook.onmicrosoft.com",
            "origin": "aad",
            "originId": "6a80ba20-a9de-46d1-8e54-c7ce08dcf2ad",
            "displayName": "František Kupka",
            "_links": {
                "self": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.NDM4NTI0NDktNTZlNy03N2Y0LTg0ZjEtNDEzNjNkNThmZDY5"
                },
                "memberships": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Memberships/aad.NDM4NTI0NDktNTZlNy03N2Y0LTg0ZjEtNDEzNjNkNThmZDY5"
                },
                "membershipState": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/MembershipStates/aad.NDM4NTI0NDktNTZlNy03N2Y0LTg0ZjEtNDEzNjNkNThmZDY5"
                },
                "storageKey": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/StorageKeys/aad.NDM4NTI0NDktNTZlNy03N2Y0LTg0ZjEtNDEzNjNkNThmZDY5"
                },
                "avatar": {
                    "href": "https://dev.azure.com/gitlab-ps/_apis/GraphProfile/MemberAvatars/aad.NDM4NTI0NDktNTZlNy03N2Y0LTg0ZjEtNDEzNjNkNThmZDY5"
                }
            },
            "url": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.NDM4NTI0NDktNTZlNy03N2Y0LTg0ZjEtNDEzNjNkNThmZDY5",
            "descriptor": "aad.NDM4NTI0NDktNTZlNy03N2Y0LTg0ZjEtNDEzNjNkNThmZDY5"
        }

        mock_get_user.return_value = user_data

        mongo = CongregateMongoConnector(client=mongomock.MongoClient)
        users.handle_retrieving_user(user_data, mongo=mongo)

        actual_users = [d for d, _ in mongo.stream_collection(
            "users-dev.azure.com")]

        self.assertEqual(len(actual_users), 1)
        self.assertEqual(actual_users[0]["username"], "frantisek.kupka")
        self.assertEqual(actual_users[0]["name"], "Frantisek Kupka")

    @patch.object(CongregateMongoConnector, "close_connection")
    @patch.object(UsersApi, "get_user")
    @patch('congregate.helpers.conf.Config.source_token',
            new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
            new_callable=PropertyMock)
    def test_create_valid_username_and_name_from_german(
        self, mock_ext_src_url, mock_ext_user_token, mock_get_user, mock_close_connection):
        users = UsersClient()
        mock_ext_src_url.return_value = "https://dev.azure.com/gitlab-ps"
        mock_ext_user_token.return_value = "username:password"
        mock_close_connection.return_value = None

        user_data = {
            "subjectKind": "user",
            "directoryAlias": "Michael.Messing",
            "domain": "7cfe4c9f-829b-4857-89f9-dfa21e53e1d9",
            "principalName": "Michael.Messing@gitlabpsoutlook.onmicrosoft.com",
            "mailAddress": "Michael.Messing@gitlabpsoutlook.onmicrosoft.com",
            "origin": "aad",
            "originId": "d19cc4b3-7772-4e25-8901-7f0b65c0b44b",
            "displayName": "Michael Meßing",
            "_links": {
                "self": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.ZjlkNWY3NjgtNmQ1MS03MGU2LTlmNzMtOThmZmZiY2I0ZmI2"
                },
                "memberships": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Memberships/aad.ZjlkNWY3NjgtNmQ1MS03MGU2LTlmNzMtOThmZmZiY2I0ZmI2"
                },
                "membershipState": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/MembershipStates/aad.ZjlkNWY3NjgtNmQ1MS03MGU2LTlmNzMtOThmZmZiY2I0ZmI2"
                },
                "storageKey": {
                    "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/StorageKeys/aad.ZjlkNWY3NjgtNmQ1MS03MGU2LTlmNzMtOThmZmZiY2I0ZmI2"
                },
                "avatar": {
                    "href": "https://dev.azure.com/gitlab-ps/_apis/GraphProfile/MemberAvatars/aad.ZjlkNWY3NjgtNmQ1MS03MGU2LTlmNzMtOThmZmZiY2I0ZmI2"
                }
            },
            "url": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.ZjlkNWY3NjgtNmQ1MS03MGU2LTlmNzMtOThmZmZiY2I0ZmI2",
            "descriptor": "aad.ZjlkNWY3NjgtNmQ1MS03MGU2LTlmNzMtOThmZmZiY2I0ZmI2"
        }

        mock_get_user.return_value = user_data

        mongo = CongregateMongoConnector(client=mongomock.MongoClient)
        users.handle_retrieving_user(user_data, mongo=mongo)

        actual_users = [d for d, _ in mongo.stream_collection(
            "users-dev.azure.com")]

        self.assertEqual(len(actual_users), 1)
        self.assertEqual(actual_users[0]["username"], "michael.messing")
        self.assertEqual(actual_users[0]["name"], "Michael Messing")
