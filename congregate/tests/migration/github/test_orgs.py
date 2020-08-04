import unittest
from mock import patch, PropertyMock, MagicMock

from congregate.tests.mockapi.github.orgs import MockOrgsApi
from congregate.tests.mockapi.github.repos import MockReposApi
from congregate.migration.github.orgs import OrgsClient
from congregate.migration.github.api.orgs import OrgsApi


class ReposTests(unittest.TestCase):
    def setUp(self):
        self.mock_orgs = MockOrgsApi()
        self.mock_repos = MockReposApi()
        self.orgs = OrgsClient()

    @patch.object(OrgsApi, "get_org")
    @patch.object(OrgsApi, "get_all_org_repos")
    # @patch.object(OrgsApi, "get_all_org_members")
    @patch.object(OrgsApi, "get_all_org_team_repos")
    # @patch.object(OrgsApi, "get_all_org_team_members")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    @patch("congregate.helpers.conf.Config.source_token", new_callable=PropertyMock)
    def test_add_org_as_group(self,
                              mock_source_token,
                              mock_source_host,
                              # mock_org_team_members,
                              mock_org_team_repos,
                              # mock_org_members,
                              mock_org_repos,
                              mock_org_response):
        mock_org = MagicMock()
        type(mock_org).status_code = PropertyMock(return_value=200)
        mock_org.json.return_value = self.mock_orgs.get_org()
        mock_org_response.return_value = mock_org
        mock_source_token.return_value = "token"
        mock_source_host.return_value = "https://github.com"
        # mock_org_members.return_value = self.mock_orgs.get_all_org_members()
        mock_org_team_repos.return_value = self.mock_orgs.get_all_org_team_repos()
        # mock_org_team_members.return_value = self.mock_orgs.get_all_org_team_members()
        mock_org_repos.return_value = self.mock_orgs.get_all_org_repos()

        expected_projects = [
            {
                "name": "googleapis",
                "members": [],
                "path": "googleapis",
                "path_with_namespace": "org1/googleapis",
                "namespace": {
                    "path": "org1",
                    "kind": "group",
                    "id": 8,
                    "full_path": "org1",
                    "name": "org1"
                },
                "id": 5,
                "visibility": "public",
                "description": None
            },
            {
                "name": "gradio",
                "members": [],
                "path": "gradio",
                "path_with_namespace": "org1/gradio",
                "namespace": {
                    "path": "org1",
                    "kind": "group",
                    "id": 8,
                    "full_path": "org1",
                    "name": "org1"
                },
                "id": 6,
                "visibility": "private",
                "description": None
            }
        ]

        expected_groups = [
            {
                "members": [],
                "parent_id": None,
                "visibility": "private",
                "name": "org1",
                "auto_devops_enabled": False,
                "path": "org1",
                "projects": expected_projects,
                "id": 8,
                "full_path": "org1",
                "description": None
            }
        ]

        actual = self.orgs.add_org_as_group(
            [self.mock_orgs.get_org()], "org1", [])

        self.assertEqual(actual[0].sort(key=lambda x: x["id"]),
                         expected_groups.sort(key=lambda x: x["id"]))
        self.assertEqual(actual[1].sort(key=lambda x: x["id"]),
                         expected_projects.sort(key=lambda x: x["id"]))

    @patch.object(OrgsApi, "get_org")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    @patch("congregate.helpers.conf.Config.source_token", new_callable=PropertyMock)
    def test_add_org_as_group_error(self,
                                    mock_source_token,
                                    mock_source_host,
                                    mock_org_response):
        mock_org = MagicMock()
        type(mock_org).status_code = PropertyMock(return_value=404)
        mock_org.json.return_value = {
            "message": "Not Found",
            "documentation_url": "https://developer.github.com/enterprise/2.21/v3"
        }
        mock_org_response.return_value = mock_org
        mock_source_token.return_value = "token"
        mock_source_host.return_value = "https://github.com"

        expected_groups, expected_projects = [], []

        actual = self.orgs.add_org_as_group([], "org1", [])

        self.assertEqual(actual[0], expected_groups)
        self.assertEqual(actual[1], expected_projects)

        expected_groups = None

        actual = self.orgs.add_org_as_group(None, "org1", [])

        self.assertEqual(actual[0], expected_groups)
        self.assertEqual(actual[1], expected_projects)

    def test_add_team_as_subgroup_error(self):
        mock_team = {
            "message": "Not Found",
            "documentation_url": "https://developer.github.com/enterprise/2.21/v3"
        }

        expected_groups, expected_projects = [], []

        actual = self.orgs.add_team_as_subgroup([], "org1", mock_team, [])

        self.assertEqual(actual[0], expected_groups)
        self.assertEqual(actual[1], expected_projects)

        mock_team = self.mock_orgs.get_all_org_teams()[1]

        expected_groups = None

        actual = self.orgs.add_team_as_subgroup(None, "org1", mock_team, [])

        self.assertEqual(actual[0], expected_groups)
        self.assertEqual(actual[1], expected_projects)

    @patch.object(OrgsApi, "get_all_org_team_repos")
    # @patch.object(OrgsApi, "get_all_org_team_members")
    @patch.object(OrgsApi, "get_org_team")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    @patch("congregate.helpers.conf.Config.source_token", new_callable=PropertyMock)
    def test_add_team_as_subgroup_team_error(self,
                                             mock_source_token,
                                             mock_source_host,
                                             mock_org_team,
                                             #    mock_org_team_members,
                                             mock_org_team_repos):

        mock_source_token.return_value = "token"
        mock_source_host.return_value = "https://github.com"
        mock_team = MagicMock()
        type(mock_team).status_code = PropertyMock(return_value=200)
        mock_team.json.return_value = self.mock_orgs.get_org_team()
        mock_team_error = MagicMock()
        type(mock_team_error).status_code = PropertyMock(return_value=404)
        mock_team_error.json.return_value = {
            "message": "Not Found",
            "documentation_url": "https://developer.github.com/enterprise/2.21/v3"
        }
        mock_org_team.side_effect = [mock_team, mock_team_error]
        # mock_org_team_members.return_value = self.mock_orgs.get_all_org_team_members()
        mock_org_team_repos.return_value = self.mock_orgs.get_all_org_team_repos()

        expected_projects = [
            {
                "name": "arrow",
                "members": [],
                "path": "arrow",
                "path_with_namespace": "org2/arrow",
                "namespace": {
                    "path": "org2",
                    "kind": "group",
                    "id": 9,
                    "full_path": "org2",
                    "name": "org2"
                },
                "id": 8,
                "visibility": "public",
                "description": None
            },
            {
                "name": "phaser",
                "members": [],
                "path": "phaser",
                "path_with_namespace": "org2/phaser",
                "namespace": {
                    "path": "org2",
                    "kind": "group",
                    "id": 9,
                    "full_path": "org2",
                    "name": "org2"
                },
                "id": 9,
                "visibility": "private",
                "description": None
            }
        ]

        expected_groups = [
            {
                "members": [],
                "parent_id": None,
                "visibility": "private",
                "name": "org2",
                "auto_devops_enabled": False,
                "path": "org2",
                "projects": expected_projects,
                "id": 9,
                "full_path": None,
                "description": None
            }
        ]

        actual = self.orgs.add_team_as_subgroup(
            [], "org1", self.mock_orgs.get_org_child_team(), [])

        self.assertEqual(actual[0].sort(key=lambda x: x["id"]),
                         expected_groups.sort(key=lambda x: x["id"]))
        self.assertEqual(actual[1].sort(key=lambda x: x["id"]),
                         expected_projects.sort(key=lambda x: x["id"]))

    @patch.object(OrgsApi, "get_all_org_team_repos")
    # @patch.object(OrgsApi, "get_all_org_team_members")
    @patch.object(OrgsApi, "get_org_team")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    @patch("congregate.helpers.conf.Config.source_token", new_callable=PropertyMock)
    def test_add_team_as_subgroup(self,
                                  mock_source_token,
                                  mock_source_host,
                                  mock_org_team,
                                  #    mock_org_team_members,
                                  mock_org_team_repos):

        mock_source_token.return_value = "token"
        mock_source_host.return_value = "https://github.com"
        mock_team = MagicMock()
        type(mock_team).status_code = PropertyMock(return_value=200)
        mock_team.json.return_value = self.mock_orgs.get_org_team()
        mock_child_team = MagicMock()
        type(mock_child_team).status_code = PropertyMock(return_value=200)
        mock_child_team.json.return_value = self.mock_orgs.get_org_child_team()
        mock_org_team.side_effect = [mock_child_team, mock_team]
        # mock_org_team_members.return_value = self.mock_orgs.get_all_org_team_members()
        mock_org_team_repos.return_value = self.mock_orgs.get_all_org_team_repos()

        expected_projects = [
            {
                "name": "arrow",
                "members": [],
                "path": "arrow",
                "path_with_namespace": "org2/arrow",
                "namespace": {
                    "path": "org2",
                    "kind": "group",
                    "id": 9,
                    "full_path": "org2",
                    "name": "org2"
                },
                "id": 8,
                "visibility": "public",
                "description": None
            },
            {
                "name": "phaser",
                "members": [],
                "path": "phaser",
                "path_with_namespace": "org2/phaser",
                "namespace": {
                    "path": "org2",
                    "kind": "group",
                    "id": 9,
                    "full_path": "org2",
                    "name": "org2"
                },
                "id": 9,
                "visibility": "private",
                "description": None
            }
        ]

        expected_groups = [
            {
                "members": [],
                "parent_id": None,
                "visibility": "private",
                "name": "org2",
                "auto_devops_enabled": False,
                "path": "org2",
                "projects": expected_projects,
                "id": 9,
                "full_path": "org2/qa/qa-child",
                "description": None
            }
        ]

        actual = self.orgs.add_team_as_subgroup(
            [], "org1", self.mock_orgs.get_org_child_team(), [])

        self.assertEqual(actual[0].sort(key=lambda x: x["id"]),
                         expected_groups.sort(key=lambda x: x["id"]))
        self.assertEqual(actual[1].sort(key=lambda x: x["id"]),
                         expected_projects.sort(key=lambda x: x["id"]))
