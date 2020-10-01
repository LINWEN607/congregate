import unittest
import pytest
from mock import patch, PropertyMock, MagicMock
import warnings
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock

from congregate.helpers.mdbc import MongoConnector
from congregate.tests.mockapi.github.orgs import MockOrgsApi
from congregate.tests.mockapi.github.repos import MockReposApi
from congregate.tests.mockapi.github.teams import MockTeamsApi
from congregate.migration.github.orgs import OrgsClient
from congregate.migration.github.repos import ReposClient
from congregate.migration.github.users import UsersClient
from congregate.migration.github.api.orgs import OrgsApi
from congregate.migration.github.api.teams import TeamsApi

@pytest.mark.unit_test
class OrgsTests(unittest.TestCase):
    def setUp(self):
        self.mock_orgs = MockOrgsApi()
        self.mock_repos = MockReposApi()
        self.mock_teams = MockTeamsApi()
        self.orgs = self.mock_org_client()

    def tearDown(self):
        self.orgs.mongo.drop_collection("projects")
        self.orgs.mongo.drop_collection("groups")
        self.orgs.mongo.drop_collection("users")

    @patch.object(OrgsApi, "get_org")
    @patch.object(OrgsApi, "get_all_org_repos")
    @patch.object(UsersClient, "format_users")
    @patch.object(ReposClient, "add_repo_members")
    @patch.object(OrgsApi, "get_all_org_members")
    @patch.object(ReposClient, "list_ci_sources_jenkins")
    @patch.object(ReposClient, "list_ci_sources_teamcity")
    def test_add_org_as_group(self,
                              mock_ci_sources1,
                              mock_ci_sources2,
                              mock_org_members,
                              mock_add_repo_members,
                              mock_format_users,
                              mock_org_repos,
                              mock_org_response):
        self.maxDiff = None
        mock_ci_sources1.return_value = []
        mock_ci_sources2.return_value = ['test-job1', 'test-job2']
        
        mock_org = MagicMock()
        type(mock_org).status_code = PropertyMock(return_value=200)
        mock_org.json.return_value = self.mock_orgs.get_org()
        mock_org_response.return_value = mock_org

        mock_org_members.return_value = self.mock_orgs.get_all_org_members()
        mock_org_repos.return_value = [(r, True) for r in self.mock_orgs.get_all_org_repos()]

        repo_members = [
            {
                "username": "bmay",
                "name": None,
                "id": 5,
                "state": "active",
                "avatar_url": "",
                "is_admin": False,
                "email": None
            },
            {
                "username": "gitlab",
                "name": None,
                "id": 3,
                "state": "active",
                "avatar_url": "",
                "is_admin": True,
                "email": None
            }
        ]

        mock_add_repo_members.side_effect = [repo_members, repo_members]

        org_members = [
            {
                "username": "bmay",
                "name": None,
                "id": 5,
                "state": "active",
                "avatar_url": "",
                "is_admin": False,
                "email": None
            },
            {
                "username": "gitlab",
                "name": None,
                "id": 3,
                "state": "active",
                "avatar_url": "",
                "is_admin": True,
                "email": None
            },
            {
                "username": "mlindsay",
                "name": None,
                "id": 4,
                "state": "active",
                "avatar_url": "",
                "is_admin": True,
                "email": None
            },
            {
                "username": "nperic",
                "name": "Nicki Peric",
                "id": 7,
                "state": "active",
                "avatar_url": "",
                "is_admin": True,
                "email": None
            }
        ]

        mock_format_users.return_value = org_members

        expected_projects = [
            {
                "name": "googleapis",
                "members": repo_members,
                "path": "googleapis",
                "path_with_namespace": "org1/googleapis",
                "http_url_to_repo": "https://github.gitlab-proserv.net/org1/googleapis.git",
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
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
                "members": repo_members,
                "path": "gradio",
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
                "path_with_namespace": "org1/gradio",
                "http_url_to_repo": "https://github.gitlab-proserv.net/org1/gradio.git",
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
                "members": org_members,
                "parent_id": None,
                "visibility": "private",
                "name": "org1",
                "auto_devops_enabled": False,
                "path": "org1",
                "projects": [
                    {
                        "name": "googleapis",
                        "members": [],
                        "path": "googleapis",
                        "path_with_namespace": "org1/googleapis",
                        "http_url_to_repo": "https://github.gitlab-proserv.net/org1/googleapis.git",
                        "ci_sources": {
                            "Jenkins": ['test-job1', 'test-job2'],
                            "TeamCity": []
                        },
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
                        "http_url_to_repo": "https://github.gitlab-proserv.net/org1/gradio.git",
                        "ci_sources": {
                            "Jenkins": ['test-job1', 'test-job2'],
                            "TeamCity": []
                        },
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
                ],
                "id": 8,
                "full_path": "org1",
                "description": None
            }
        ]

        self.orgs.add_org_as_group(
            [self.mock_orgs.get_org()], "org1", [])
        
        actual_groups = [d for d, _ in self.orgs.mongo.stream_collection("groups")]
        actual_projects = [d for d, _ in self.orgs.mongo.stream_collection("projects")]

        for i in range(len(expected_groups)):
            self.assertDictEqual(
                actual_groups[i], expected_groups[i]
            )
        for i in range(len(expected_projects)):
            self.assertDictEqual(
                actual_projects[i], expected_projects[i]
            )

    @patch.object(OrgsApi, "get_org")
    def test_add_org_as_group_error(self, mock_org_response):
        mock_org = MagicMock()
        type(mock_org).status_code = PropertyMock(return_value=404)
        mock_org.json.return_value = {
            "message": "Not Found",
            "documentation_url": "https://developer.github.com/enterprise/2.21/v3"
        }
        mock_org_response.return_value = mock_org

        actual = self.orgs.add_org_as_group([], "org1", [])

        self.assertLogs(
            "Failed to append org {} ({}) to list {}".format("org1", mock_org, []))

        expected_groups = None

        actual = self.orgs.add_org_as_group(None, "org1", [])

        self.assertLogs("Failed to append org {} ({}) to list {}".format(
            "org1", mock_org, None))

    def test_add_team_as_subgroup_error(self):
        mock_team = {
            "message": "Not Found",
            "documentation_url": "https://developer.github.com/enterprise/2.21/v3"
        }
        mock_org = self.mock_orgs.get_all_orgs()[0]

        expected_groups, expected_projects = [], []

        actual_groups = [d for d, _ in self.orgs.mongo.stream_collection("groups")]
        actual_projects = [d for d, _ in self.orgs.mongo.stream_collection("projects")]

        self.orgs.add_team_as_subgroup(mock_org, mock_team, [])

        self.assertEqual(actual_groups, expected_groups)
        self.assertEqual(actual_projects, expected_projects)
        self.assertLogs(
            "Failed to store team {}".format(mock_team))

    @patch.object(TeamsApi, "get_team_repos")
    @patch.object(TeamsApi, "get_team_members")
    @patch.object(UsersClient, "format_users")
    @patch.object(ReposClient, "add_repo_members")
    @patch.object(OrgsApi, "get_org_team")
    @patch.object(ReposClient, "list_ci_sources_jenkins")
    @patch.object(ReposClient, "list_ci_sources_teamcity")
    def test_add_team_as_subgroup_team_error(self,
                                             mock_ci_sources1,
                                             mock_ci_sources2,
                                             mock_org_team,
                                             mock_add_repo_members,
                                             mock_format_users,
                                             mock_org_team_members,
                                             mock_team_repos):

        mock_ci_sources1.return_value = []
        mock_ci_sources2.return_value = ['test-job1', 'test-job2']
        
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

        mock_org_team_members.return_value = self.mock_orgs.get_all_org_team_members()
        mock_team_repos.return_value = self.mock_teams.get_all_team_repos()
        mock_org = self.mock_orgs.get_all_orgs()[1]

        org_team_repo_members = [
            {
                "username": "gitlab",
                "name": None,
                "id": 3,
                "state": "active",
                "avatar_url": "",
                "is_admin": True,
                "email": None
            },
            {
                "id": 6,
                "username": "pprokic",
                "name": "Petar Prokic",
                "email": "pprokic@gitlab.com",
                "avatar_url": "",
                "state": "active",
                "is_admin": False,
                "access_level": 20
            }
        ]

        mock_format_users.return_value = org_team_repo_members
        mock_add_repo_members.side_effect = [
            org_team_repo_members, org_team_repo_members]

        expected_projects = [
            {
                "id": 8,
                "path": "arrow",
                "name": "arrow",
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
                "namespace": {
                    "id": 9,
                    "path": "org2",
                    "name": "org2",
                    "kind": "group",
                    "full_path": "org2"
                },
                "path_with_namespace": "org2/arrow",
                "http_url_to_repo": "https://github.gitlab-proserv.net/org2/arrow.git",
                "visibility": "public",
                "description": None,
                "members": org_team_repo_members
            },
            {
                "id": 9,
                "path": "phaser",
                "name": "phaser",
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
                "namespace": {
                    "id": 9,
                    "path": "org2",
                    "name": "org2",
                    "kind": "group",
                    "full_path": "org2"
                },
                "path_with_namespace": "org2/phaser",
                "http_url_to_repo": "https://github.gitlab-proserv.net/org2/phaser.git",
                "visibility": "private",
                "description": None,
                "members": org_team_repo_members
            }
        ]

        expected_groups = [
            {
                "members": org_team_repo_members,
                "parent_id": None,
                "visibility": "private",
                "name": "qa-child",
                "auto_devops_enabled": False,
                "path": "qa-child",
                "projects": [
                    {
                        "id": 8,
                        "path": "arrow",
                        "name": "arrow",
                        "ci_sources": {
                            "Jenkins": ['test-job1', 'test-job2'],
                            "TeamCity": []
                        },
                        "namespace": {
                            "id": 9,
                            "path": "org2",
                            "name": "org2",
                            "kind": "group",
                            "full_path": "org2"
                        },
                        "path_with_namespace": "org2/arrow",
                        "http_url_to_repo": "https://github.gitlab-proserv.net/org2/arrow.git",
                        "visibility": "public",
                        "description": None,
                        "members": []
                    },
                    {
                        "id": 9,
                        "path": "phaser",
                        "name": "phaser",
                        "ci_sources": {
                            "Jenkins": ['test-job1', 'test-job2'],
                            "TeamCity": []
                        },
                        "namespace": {
                            "id": 9,
                            "path": "org2",
                            "name": "org2",
                            "kind": "group",
                            "full_path": "org2"
                        },
                        "path_with_namespace": "org2/phaser",
                        "http_url_to_repo": "https://github.gitlab-proserv.net/org2/phaser.git",
                        "visibility": "private",
                        "description": None,
                        "members": []
                    }
                ],
                "id": 9,
                "full_path": None,
                "description": None
            }
        ]

        self.orgs.add_team_as_subgroup(mock_org, self.mock_orgs.get_org_child_team(), [])

        actual_groups = [d for d, _ in self.orgs.mongo.stream_collection("groups")]
        actual_projects = [d for d, _ in self.orgs.mongo.stream_collection("projects")]

        self.assertEqual(actual_groups.sort(key=lambda x: x["id"]),
                         expected_groups.sort(key=lambda x: x["id"]))
        
        self.assertLogs("Failed to get full_path for team ({})".format(
            self.mock_orgs.get_org_child_team()))
        
        for i in range(len(expected_projects)):
            self.assertDictEqual(
                actual_projects[i], expected_projects[i]
            )

    @patch.object(TeamsApi, "get_team_repos")
    @patch.object(TeamsApi, "get_team_members")
    @patch.object(UsersClient, "format_users")
    @patch.object(ReposClient, "add_repo_members")
    @patch.object(OrgsApi, "get_org_team")
    @patch.object(ReposClient, "list_ci_sources_jenkins")
    @patch.object(ReposClient, "list_ci_sources_teamcity")
    def test_add_team_as_subgroup(self,
                                  mock_ci_sources1,
                                  mock_ci_sources2,
                                  mock_org_team,
                                  mock_add_repo_members,
                                  mock_format_users,
                                  mock_org_team_members,
                                  mock_org_team_repos):

        mock_ci_sources1.return_value = []
        mock_ci_sources2.return_value = ['test-job1', 'test-job2']
      
        mock_team = MagicMock()
        type(mock_team).status_code = PropertyMock(return_value=200)
        mock_team.json.return_value = self.mock_orgs.get_org_team()
        mock_child_team = MagicMock()
        type(mock_child_team).status_code = PropertyMock(return_value=200)
        mock_child_team.json.return_value = self.mock_orgs.get_org_child_team()
        mock_org_team.side_effect = [mock_child_team, mock_team]

        mock_org_team_members.return_value = self.mock_orgs.get_all_org_team_members()
        mock_org_team_repos.return_value = self.mock_teams.get_all_team_repos()
        mock_org = self.mock_orgs.get_all_orgs()[1]

        org_team_repo_members = [
            {
                "username": "gitlab",
                "name": None,
                "id": 3,
                "state": "active",
                "avatar_url": "",
                "is_admin": True,
                "email": None
            },
            {
                "id": 6,
                "username": "pprokic",
                "name": "Petar Prokic",
                "email": "pprokic@gitlab.com",
                "avatar_url": "",
                "state": "active",
                "is_admin": False,
                "access_level": 20
            }
        ]

        mock_format_users.return_value = org_team_repo_members
        mock_add_repo_members.side_effect = [
            org_team_repo_members, org_team_repo_members]

        expected_projects = [
            {
                "id": 8,
                "path": "arrow",
                "name": "arrow",
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
                "namespace": {
                    "id": 9,
                    "path": "org2",
                    "name": "org2",
                    "kind": "group",
                    "full_path": "org2"
                },
                "path_with_namespace": "org2/arrow",
                "http_url_to_repo": "https://github.gitlab-proserv.net/org2/arrow.git",
                "visibility": "public",
                "description": None,
                "members": org_team_repo_members
            },
            {
                "id": 9,
                "path": "phaser",
                "name": "phaser",
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
                "namespace": {
                    "id": 9,
                    "path": "org2",
                    "name": "org2",
                    "kind": "group",
                    "full_path": "org2"
                },
                "path_with_namespace": "org2/phaser",
                "http_url_to_repo": "https://github.gitlab-proserv.net/org2/phaser.git",
                "visibility": "private",
                "description": None,
                "members": org_team_repo_members
            }
        ]

        expected_groups = [
            {
                "members": org_team_repo_members,
                "parent_id": None,
                "visibility": "private",
                "name": "qa-child",
                "auto_devops_enabled": False,
                "path": "qa-child",
                "projects": [
                    {
                        "id": 8,
                        "path": "arrow",
                        "name": "arrow",
                        "ci_sources": {
                            "Jenkins": ['test-job1', 'test-job2'],
                            "TeamCity": []
                        },
                        "namespace": {
                            "id": 9,
                            "path": "org2",
                            "name": "org2",
                            "kind": "group",
                            "full_path": "org2"
                        },
                        "path_with_namespace": "org2/arrow",
                        "http_url_to_repo": "https://github.gitlab-proserv.net/org2/arrow.git",
                        "visibility": "public",
                        "description": None,
                        "members": []
                    },
                    {
                        "id": 9,
                        "path": "phaser",
                        "name": "phaser",
                        "ci_sources": {
                            "Jenkins": ['test-job1', 'test-job2'],
                            "TeamCity": []
                        },
                        "namespace": {
                            "id": 9,
                            "path": "org2",
                            "name": "org2",
                            "kind": "group",
                            "full_path": "org2"
                        },
                        "path_with_namespace": "org2/phaser",
                        "http_url_to_repo": "https://github.gitlab-proserv.net/org2/phaser.git",
                        "visibility": "private",
                        "description": None,
                        "members": []
                    }
                ],
                "id": 9,
                "full_path": "org2/qa/qa-child",
                "description": None
            }
        ]

        self.orgs.add_team_as_subgroup(
            mock_org, self.mock_orgs.get_org_child_team(), [])

        actual_groups = [d for d, _ in self.orgs.mongo.stream_collection("groups")]
        
        actual_projects = [d for d, _ in self.orgs.mongo.stream_collection("projects")]

        self.assertEqual(actual_groups.sort(key=lambda x: x["id"]),
                         expected_groups.sort(key=lambda x: x["id"]))
        for i in range(len(expected_projects)):
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())


    def mock_org_client(self):
        with patch.object(OrgsClient, "connect_to_mongo") as mongo_mock:
            with patch.object(UsersClient, "connect_to_mongo") as mongo_mock_2:
                mongo_mock_2.return_value = MongoConnector(host="test-server", port=123456, client=mongomock.MongoClient)
                mongo_mock.return_value = MongoConnector(host="test-server", port=123456, client=mongomock.MongoClient)
                return OrgsClient()