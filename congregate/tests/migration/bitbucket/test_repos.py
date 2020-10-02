import unittest
import pytest
from mock import patch, PropertyMock, MagicMock

from congregate.tests.mockapi.bitbucket.repos import MockReposApi
from congregate.migration.bitbucket.repos import ReposClient
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.tests.mockapi.bitbucket.groups import MockGroupsApi


@pytest.mark.unit_test
class ReposTests(unittest.TestCase):
    def setUp(self):
        self.mock_repos = MockReposApi()
        self.repos = ReposClient()
        self.mock_groups = MockGroupsApi()

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(ReposApi, "get_all_repos")
    @patch.object(ReposApi, "get_all_repo_users")
    @patch.object(ReposApi, "get_repo_default_branch")
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_retrieve_repo_info(self, mock_ext_user_token, mock_ext_src_url, mock_branch, mock_get_all_repo_users, mock_get_all_repos, mock_open, mock_file):
        mock_ext_src_url.return_value = "http://localhost:7990"
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
        mock_open.return_value = mock_file
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
                "default_branch": "develop",
                "path": "android",
                "path_with_namespace": "TGP/android",
                "visibility": "private",
                "description": "",
                "id": 6
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
                "default_branch": "master",
                "path": "another-test-repo",
                "path_with_namespace": "ATP/another-test-repo",
                "visibility": "private",
                "description": "Just another test repo",
                "id": 13
            }
        ]
        actual_repos = self.repos.retrieve_repo_info()
        for i, _ in enumerate(expected_repos):
            self.assertEqual(
                actual_repos[i].items(), expected_repos[i].items())

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(ReposApi, "get_all_repos")
    @patch.object(ReposApi, "get_all_repo_users")
    @patch.object(ReposApi, "get_all_repo_groups")
    @patch.object(ReposApi, "get_repo_default_branch")
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_retrieve_repo_info_with_groups(self, mock_ext_user_token, mock_ext_src_url, mock_branch, mock_get_all_repo_groups, mock_get_all_repo_users, mock_get_all_repos, mock_open, mock_file):
        mock_ext_src_url.return_value = "http://localhost:7990"
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
        mock_open.return_value = mock_file
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
                "default_branch": "develop",
                "path": "android",
                "path_with_namespace": "TGP/android",
                "visibility": "private",
                "description": "",
                "id": 6
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
                "default_branch": "master",
                "path": "another-test-repo",
                "path_with_namespace": "ATP/another-test-repo",
                "visibility": "private",
                "description": "Just another test repo",
                "id": 13
            }
        ]

        actual_repos = self.repos.retrieve_repo_info(groups=groups)
        for i, _ in enumerate(expected_repos):
            self.assertEqual(
                actual_repos[i].items(), expected_repos[i].items())
