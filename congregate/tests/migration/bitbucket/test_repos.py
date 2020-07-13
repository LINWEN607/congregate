import unittest
from mock import patch, PropertyMock

from congregate.tests.mockapi.bitbucket.repos import MockReposApi
from congregate.migration.bitbucket.repos import ReposClient
from congregate.migration.bitbucket.api.repos import ReposApi


class ReposTests(unittest.TestCase):
    def setUp(self):
        self.mock_repos = MockReposApi()
        self.repos = ReposClient()

    @patch("__builtin__.file")
    @patch('__builtin__.open')
    @patch.object(ReposApi, "get_all_repos")
    @patch.object(ReposApi, "get_all_repo_users")
    @patch('congregate.helpers.conf.Config.external_source_url', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.external_access_token', new_callable=PropertyMock)
    def test_retrieve_repo_info(self, mock_ext_user_token, mock_ext_src_url, mock_get_all_repo_users, mock_get_all_repos, mock_open, mock_file):
        mock_ext_src_url.return_value = "http://localhost:7990"
        mock_ext_user_token.return_value = "username:password"
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
                    "web_url": "http://localhost:7990/projects/TGP",
                    "path": "TGP",
                    "id": 1,
                    "full_path": "TGP"
                },
                "members": [
                    {
                        "username": "user2",
                        "web_url": "http://localhost:7990/users/user2",
                        "id": 3,
                        "name": "user2",
                        "access_level": 20,
                        "state": "active",
                        "email": "user2@example.com"
                    },
                    {
                        "username": "user4",
                        "web_url": "http://localhost:7990/users/user4",
                        "id": 5,
                        "name": "user4",
                        "access_level": 20,
                        "state": "active",
                        "email": "user4@example.com"
                    }
                ],
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
                    "web_url": "http://localhost:7990/projects/ATP",
                    "path": "ATP",
                    "id": 22,
                    "full_path": "ATP"
                },
                "members": [
                    {
                        "username": "user2",
                        "web_url": "http://localhost:7990/users/user2",
                        "id": 3,
                        "name": "user2",
                        "access_level": 20,
                        "state": "active",
                        "email": "user2@example.com"
                    },
                    {
                        "username": "user4",
                        "web_url": "http://localhost:7990/users/user4",
                        "id": 5,
                        "name": "user4",
                        "access_level": 20,
                        "state": "active",
                        "email": "user4@example.com"
                    }
                ],
                "path": "another-test-repo",
                "path_with_namespace": "ATP/another-test-repo",
                "visibility": "private",
                "description": "Just another test repo",
                "id": 13
            }
        ]
        self.assertEqual(sorted(self.repos.retrieve_repo_info()),
                         sorted(expected_repos))
