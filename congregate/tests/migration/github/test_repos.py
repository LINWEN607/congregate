import unittest
from mock import patch, PropertyMock

from congregate.tests.mockapi.github.repos import MockReposApi
from congregate.migration.github.repos import ReposClient
from congregate.migration.github.api.repos import ReposApi


class ReposTests(unittest.TestCase):

    def setUp(self):
        self.mock_repos = MockReposApi()
        self.repos = ReposClient()

    @patch("__builtin__.file")
    @patch("__builtin__.open")
    @patch.object(ReposApi, "get_all_public_repos")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    @patch("congregate.helpers.conf.Config.source_token", new_callable=PropertyMock)
    def test_retrieve_org_info(self,
                               mock_source_token,
                               mock_source_host,
                               mock_public_repos,
                               mock_open,
                               mock_file):

        mock_source_token.return_value = "token"
        mock_source_host.return_value = "https://github.com"
        mock_public_repos.return_value = self.mock_repos.get_all_public_repos()

        mock_open.return_value = mock_file

        expected_repos = [
            {
                "name": "website",
                "members": [],
                "path": "website",
                "path_with_namespace": "gitlab/website",
                "namespace": {
                    "path": "gitlab",
                    "kind": "user",
                    "id": 3,
                    "full_path": "gitlab",
                    "name": "gitlab"
                },
                "id": 1,
                "visibility": "public",
                "description": None
            },
            {
                "name": "asdf",
                "members": [],
                "path": "asdf",
                "path_with_namespace": "bmay/asdf",
                "namespace": {
                    "path": "bmay",
                    "kind": "user",
                    "id": 5,
                    "full_path": "bmay",
                    "name": "bmay"
                },
                "id": 2,
                "visibility": "public",
                "description": None
            }
        ]

        self.assertEqual(self.repos.retrieve_repo_info().sort(
            key=lambda x: x["id"]), expected_repos.sort(key=lambda x: x["id"]))
