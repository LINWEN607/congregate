import unittest
from mock import patch, PropertyMock

from congregate.tests.mockapi.github.orgs import MockOrgsApi
from congregate.migration.github.orgs import OrgsClient
from congregate.migration.github.api.orgs import OrgsApi


class ReposTests(unittest.TestCase):
    def setUp(self):
        self.mock_orgs = MockOrgsApi()
        self.orgs = OrgsClient()

    @patch("__builtin__.file")
    @patch("__builtin__.open")
    @patch.object(OrgsApi, "get_all_orgs")
    @patch.object(OrgsApi, "get_all_org_repos")
    @patch.object(OrgsApi, "get_all_org_members")
    @patch.object(OrgsApi, "get_all_org_teams")
    @patch.object(OrgsApi, "get_all_org_team_repos")
    @patch.object(OrgsApi, "get_all_org_team_members")
    @patch.object(OrgsApi, "get_all_org_child_teams")
    @patch.object(OrgsApi, "get_all_org_child_team_repos")
    @patch.object(OrgsApi, "get_all_org_child_team_members")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    @patch("congregate.helpers.conf.Config.source_token", new_callable=PropertyMock)
    def test_retrieve_org_info(self,
                               mock_source_token,
                               mock_source_host,
                               mock_org_child_team_members,
                               mock_org_child_team_repos,
                               mock_org_child_teams,
                               mock_org_team_members,
                               mock_org_team_repos,
                               mock_org_teams,
                               mock_org_members,
                               mock_org_repos,
                               mock_orgs,
                               mock_open,
                               mock_file):

        mock_source_token.return_value = "token"
        mock_source_host.return_value = "https://github.com"
        mock_orgs.return_value = self.mock_orgs.get_all_orgs()
        mock_org_repos.return_value = self.mock_orgs.get_all_org_repos()
        mock_org_members.return_value = self.mock_orgs.get_all_org_members()
        mock_org_teams.return_value = self.mock_orgs.get_all_org_teams()
        mock_org_team_repos.return_value = self.mock_orgs.get_all_org_team_repos()
        mock_org_team_members.return_value = self.mock_orgs.get_all_org_team_members()
        mock_org_child_teams.return_value = self.mock_orgs.get_all_org_child_teams()
        mock_org_child_team_repos.return_value = self.mock_orgs.get_all_org_child_team_repos()
        mock_org_child_team_members.return_value = self.mock_orgs.get_all_org_child_team_members()
        mock_open.return_value = mock_file

        expected_orgs = []

        self.assertEqual(sorted(self.orgs.retrieve_org_info()),
                         sorted(expected_orgs))
