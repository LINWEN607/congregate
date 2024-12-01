import unittest
from unittest.mock import patch, PropertyMock, MagicMock
from pytest import mark
import warnings
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock
from congregate.helpers.congregate_mdbc import CongregateMongoConnector
from congregate.tests.mockapi.bitbucket.repos import MockReposApi
from congregate.migration.bitbucket.repos import ReposClient
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.tests.mockapi.bitbucket.groups import MockGroupsApi


@mark.unit_test
class ReposTests(unittest.TestCase):
    def setUp(self):
        self.mock_repos = MockReposApi()
        self.repos = ReposClient()
        self.mock_groups = MockGroupsApi()

    @patch.object(CongregateMongoConnector, "close_connection")
    @patch.object(ReposApi, "get_all_repos")
    @patch.object(ReposApi, "get_all_repo_users")
    @patch.object(ReposApi, "get_repo_default_branch")
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_retrieve_repo_info(self, mock_ext_user_token, mock_ext_src_url, mock_branch, mock_get_all_repo_users, mock_get_all_repos, mock_close_connection):
        mock_ext_src_url.return_value = "http://bitbucket.company.com"
        mock_ext_user_token.return_value = "username:password"
        mock_branch1 = MagicMock()
        type(mock_branch1).status_code = PropertyMock(return_value=200)
        mock_branch1.json.return_value = self.mock_repos.get_repo_default_branch()
        mock_branch2 = MagicMock()
        type(mock_branch2).status_code = PropertyMock(return_value=204)
        mock_branch2.json.return_value = None
        mock_branch.side_effect = [mock_branch1, mock_branch2]
        mock_get_all_repo_users.side_effect = [
            self.mock_repos.get_all_repo_users(), self.mock_repos.get_all_repo_users()]
        mock_get_all_repos.return_value = self.mock_repos.get_all_repos()
        expected_repos = [
            {
                "name": "android",
                "namespace": {
                    "kind": "group",
                    "name": "test-group",
                    "path": "TGP",
                    "id": 1,
                    "full_path": "TGP"
                },
                "members": [
                    {
                        "username": "user2",
                        "id": 3,
                        "name": "user2",
                        "access_level": 20,
                        "state": "active",
                        "email": "user2@example.com"
                    },
                    {
                        "username": "user4",
                        "id": 5,
                        "name": "user4",
                        "access_level": 20,
                        "state": "active",
                        "email": "user4@example.com"
                    }
                ],
                "groups": {},
                "default_branch": "develop",
                "path": "android",
                "path_with_namespace": "TGP/android",
                "visibility": "private",
                "description": "",
                "id": 6,
                "archived": False,
                "http_url_to_repo": "http://localhost:7990/scm/tgp/android.git"
            },
            {
                "name": "Another-Test-Repo",
                "namespace": {
                    "kind": "group",
                    "name": "Another-Test-Project",
                    "path": "ATP",
                    "id": 22,
                    "full_path": "ATP"
                },
                "members": [
                    {
                        "username": "user2",
                        "id": 3,
                        "name": "user2",
                        "access_level": 20,
                        "state": "active",
                        "email": "user2@example.com"
                    },
                    {
                        "username": "user4",
                        "id": 5,
                        "name": "user4",
                        "access_level": 20,
                        "state": "active",
                        "email": "user4@example.com"
                    }
                ],
                "groups": {},
                "default_branch": "master",
                "path": "another-test-repo",
                "path_with_namespace": "ATP/another-test-repo",
                "visibility": "private",
                "description": "Just another test repo",
                "id": 13,
                "archived": False,
                "http_url_to_repo": "http://localhost:7990/scm/atp/another-test-repo.git"
            }
        ]

        mock_close_connection.return_value = None

        listed_project = [self.mock_repos.get_all_repos(
        )[0], self.mock_repos.get_all_repos()[1]]

        mongo = CongregateMongoConnector(client=mongomock.MongoClient)
        for project in listed_project:
            self.repos.handle_retrieving_repos(False, project, mongo=mongo)

        actual_repos = [d for d, _ in mongo.stream_collection(
            "projects-bitbucket.company.com")]

        for i, _ in enumerate(expected_repos):
            self.assertDictEqual(
                actual_repos[i], expected_repos[i])

    @patch.object(CongregateMongoConnector, "close_connection")
    @patch.object(ReposApi, "get_all_repos")
    @patch.object(ReposApi, "get_all_repo_users")
    @patch.object(ReposApi, "get_all_repo_groups")
    @patch.object(ReposApi, "get_repo_default_branch")
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_retrieve_repo_info_with_groups(self, mock_ext_user_token, mock_ext_src_url, mock_branch, mock_get_all_repo_groups, mock_get_all_repo_users, mock_get_all_repos, mock_close_connection):
        mock_ext_src_url.return_value = "http://bitbucket.company.com"
        mock_ext_user_token.return_value = "username:password"
        mock_branch1 = MagicMock()
        type(mock_branch1).status_code = PropertyMock(return_value=200)
        mock_branch1.json.return_value = self.mock_repos.get_repo_default_branch()
        mock_branch2 = MagicMock()
        type(mock_branch2).status_code = PropertyMock(return_value=204)
        mock_branch2.json.return_value = None
        mock_branch.side_effect = [mock_branch1, mock_branch2]
        mock_get_all_repo_users.side_effect = [
            self.mock_repos.get_all_repo_users(), self.mock_repos.get_all_repo_users()]
        mock_get_all_repo_groups.side_effect = [
            self.mock_repos.get_all_repo_groups(), []]
        groups = {
            "test-group": self.mock_groups.get_all_group_members()
        }
        mock_get_all_repos.return_value = self.mock_repos.get_all_repos()
        expected_repos = [
            {
                "id": 6,
                "path": "android",
                "name": "android",
                "namespace": {
                    "id": 1,
                    "path": "TGP",
                    "name": "test-group",
                    "kind": "group",
                    "full_path": "TGP"
                },
                "path_with_namespace": "TGP/android",
                "visibility": "private",
                "description": "",
                "members": [
                    {
                        "id": 3,
                        "username": "user2",
                        "name": "user2",
                        "email": "user2@example.com",
                        "state": "active",
                        "access_level": 20
                    },
                    {
                        "id": 5,
                        "username": "user4",
                        "name": "user4",
                        "email": "user4@example.com",
                        "state": "active",
                        "access_level": 20
                    },
                    {
                        "id": 1,
                        "username": "admin",
                        "name": "John Doe",
                        "email": "sysadmin@yourcompany.com",
                        "state": "active",
                        "access_level": 20
                    },
                    {
                        "id": 2,
                        "username": "user1",
                        "name": "user1",
                        "email": "user1@example.com",
                        "state": "active",
                        "access_level": 20
                    },
                    {
                        "id": 4,
                        "username": "user3",
                        "name": "user3",
                        "email": "user3@example.com",
                        "state": "active",
                        "access_level": 20
                    },
                    {
                        "id": 6,
                        "username": "user5",
                        "name": "user5",
                        "email": "user5@example.com",
                        "state": "active",
                        "access_level": 20
                    }
                ],
                "groups": {'stash-users': 20, 'test-group': 20},
                "default_branch": "develop",
                "archived": False,
                "http_url_to_repo": "http://localhost:7990/scm/tgp/android.git"
            },
            {
                "id": 13,
                "path": "another-test-repo",
                "name": "Another-Test-Repo",
                "namespace": {
                    "id": 22,
                    "path": "ATP",
                    "name": "Another-Test-Project",
                    "kind": "group",
                    "full_path": "ATP"
                },
                "path_with_namespace": "ATP/another-test-repo",
                "visibility": "private",
                "description": "Just another test repo",
                "members": [
                    {
                        "username": "user2",
                        "id": 3,
                        "name": "user2",
                        "access_level": 20,
                        "state": "active",
                        "email": "user2@example.com"
                    },
                    {
                        "username": "user4",
                        "id": 5,
                        "name": "user4",
                        "access_level": 20,
                        "state": "active",
                        "email": "user4@example.com"
                    }
                ],
                "groups": {},
                "default_branch": "master",
                "archived": False,
                "http_url_to_repo": "http://localhost:7990/scm/atp/another-test-repo.git"
            }
        ]

        mock_close_connection.return_value = None

        self.repos.set_user_groups(groups)

        listed_project = [self.mock_repos.get_all_repos(
        )[0], self.mock_repos.get_all_repos()[1]]

        mongo = CongregateMongoConnector(client=mongomock.MongoClient)
        for project in listed_project:
            self.repos.handle_retrieving_repos(False, project, mongo=mongo)

        actual_repos = [d for d, _ in mongo.stream_collection(
            "projects-bitbucket.company.com")]

        for i, _ in enumerate(expected_repos):
            self.assertDictEqual(
                actual_repos[i], expected_repos[i])
