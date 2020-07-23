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

        expected_repos = []

        self.assertEqual(sorted(self.repos.get_all_public_repos()),
                         sorted(expected_repos))
