import unittest
import warnings
from unittest.mock import patch, PropertyMock, MagicMock
from pytest import mark
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock
from congregate.helpers.congregate_mdbc import CongregateMongoConnector
from congregate.tests.mockapi.bitbucket.projects import MockProjectsApi
from congregate.migration.bitbucket.projects import ProjectsClient
from congregate.migration.bitbucket.base import BitBucketServer
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.tests.mockapi.bitbucket.groups import MockGroupsApi


@mark.unit_test
class ProjectsTests(unittest.TestCase):
    def setUp(self):
        self.mock_projects = MockProjectsApi()
        self.projects = ProjectsClient()
        self.mock_groups = MockGroupsApi()

    @patch.object(CongregateMongoConnector, "close_connection")
    @patch.object(ProjectsApi, "get_all_project_users")
    @patch.object(ProjectsApi, "get_all_project_repos")
    @patch.object(ProjectsApi, "get_all_projects")
    @patch.object(BitBucketServer, "add_repo_users")
    @patch.object(ReposApi, "get_repo_default_branch")
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_retrieve_project_info(self, mock_user_token, mock_src_host, mock_dest_url, mock_get_default_branch, mock_add_repo_users,
                                   mock_get_all_projects, mock_get_all_project_repos, mock_get_all_project_users, mock_close_connection):
        mock_dest_url.side_effect = ["http://gitlab.com", "http://gitlab.com"]
        mock_src_host.return_value = "http://bitbucket.company.com"
        mock_user_token.return_value = "username:password"
        mock_resp = MagicMock()
        type(mock_resp).status_code = PropertyMock(return_value=200)
        mock_resp.json.side_effect = [
            {"displayId": "main"}, {"displayId": "main"}, {"displayId": "main"}, {"displayId": "main"}]
        mock_get_default_branch.side_effect = [
            mock_resp, mock_resp, mock_resp, mock_resp]

        mock_add_repo_users.side_effect = [[], [], [], []]
        mock_get_all_project_repos.side_effect = [
            self.mock_projects.get_all_project_repos(), self.mock_projects.get_all_project_repos()]
        mock_get_all_project_users.side_effect = [
            self.mock_projects.get_all_project_users(), self.mock_projects.get_all_project_users()]
        mock_get_all_projects.return_value = self.mock_projects.get_all_projects()
        expected_members = [
            {
                "id": 3,
                "username": "user2",
                "name": "user2",
                "email": "user2@example.com",
                "state": "active",
                "access_level": 20
            },
            {
                "id": 1,
                "username": "user1",
                "name": "user1",
                "email": "user1@example.com",
                "state": "active",
                "access_level": 20
            }
        ]
        expected_projects = [
            {
                "name": "test-group",
                "id": 1,
                "path": "TGP",
                "full_path": "TGP",
                "visibility": "private",
                "description": "test",
                "members": expected_members,
                "groups": {},
                "projects": [3, 6]
            },
            {
                "name": "another-test-group",
                "id": 2,
                "path": "ATP",
                "full_path": "ATP",
                "visibility": "private",
                "description": "test",
                "members": expected_members,
                "groups": {},
                "projects": [3, 6]
            }
        ]

        mock_close_connection.return_value = None

        listed_project = [self.mock_projects.get_all_projects(
        )[0], self.mock_projects.get_all_projects()[1]]

        mongo = CongregateMongoConnector(client=mongomock.MongoClient)
        for project in listed_project:
            self.projects.handle_retrieving_projects(False, project, mongo=mongo)

        actual_projects = [d for d, _ in mongo.stream_collection(
            "groups-bitbucket.company.com")]
        print(actual_projects)

        for i, _ in enumerate(expected_projects):
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())

    @patch.object(CongregateMongoConnector, "close_connection")
    @patch.object(ProjectsApi, "get_all_project_groups")
    @patch.object(ProjectsApi, "get_all_project_users")
    @patch.object(ProjectsApi, "get_all_project_repos")
    @patch.object(ProjectsApi, "get_all_projects")
    @patch.object(BitBucketServer, "add_repo_users")
    @patch.object(ReposApi, "get_repo_default_branch")
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_retrieve_project_info_with_groups(self, mock_user_token, mock_src_host, mock_dest_host, mock_get_default_branch, mock_add_repo_users,
                                               mock_get_all_projects, mock_get_all_project_repos, mock_get_all_project_users, mock_get_all_project_groups, mock_close_connection):
        mock_dest_host.side_effect = [
            "http://gitlab.example.com", "http://gitlab.example.com"]
        mock_src_host.return_value = "http://bitbucket.company.com"
        mock_user_token.return_value = "username:password"
        mock_resp = MagicMock()
        type(mock_resp).status_code = PropertyMock(return_value=204)
        mock_resp.json.side_effect = [None, None, None, None]
        mock_get_default_branch.side_effect = [
            mock_resp, mock_resp, mock_resp, mock_resp]

        mock_add_repo_users.side_effect = [[], [], [], []]
        mock_get_all_project_repos.side_effect = [
            self.mock_projects.get_all_project_repos(), self.mock_projects.get_all_project_repos()]
        mock_get_all_project_users.side_effect = [
            self.mock_projects.get_all_project_users(), self.mock_projects.get_all_project_users()]
        mock_get_all_projects.return_value = self.mock_projects.get_all_projects()
        mock_get_all_project_groups.side_effect = [
            self.mock_projects.get_all_project_groups(), []]
        groups = {
            "test-group": self.mock_groups.get_all_group_members()
        }
        expected_projects = [
            {
                "name": "test-group",
                "id": 1,
                "path": "TGP",
                "full_path": "TGP",
                "visibility": "private",
                "description": "test",
                "members": [
                    {
                        "id": 3,
                        "username": "user2",
                        "name": "user2",
                        "email": "user2@example.com",
                        "state": "active",
                        "access_level": 30,
                        "index": 0
                    },
                    {
                        "id": 1,
                        "username": "admin",
                        "name": "John Doe",
                        "email": "sysadmin@yourcompany.com",
                        "state": "active",
                        "access_level": 30,
                        "index": 1
                    },
                    {
                        "id": 2,
                        "username": "user1",
                        "name": "user1",
                        "email": "user1@example.com",
                        "state": "active",
                        "access_level": 30
                    },
                    {
                        "id": 4,
                        "username": "user3",
                        "name": "user3",
                        "email": "user3@example.com",
                        "state": "active",
                        "access_level": 30
                    },
                    {
                        "id": 5,
                        "username": "user4",
                        "name": "user4",
                        "email": "user4@example.com",
                        "state": "active",
                        "access_level": 30
                    },
                    {
                        "id": 6,
                        "username": "user5",
                        "name": "user5",
                        "email": "user5@example.com",
                        "state": "active",
                        "access_level": 30
                    }
                ],
                "groups": {'stash-users': 20, 'test-group': 30},
                "projects": [3, 6]
            },
            {
                "name": "another-test-group",
                "id": 2,
                "path": "ATP",
                "full_path": "ATP",
                "visibility": "private",
                "description": "test",
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
                        "id": 1,
                        "username": "user1",
                        "name": "user1",
                        "email": "user1@example.com",
                        "state": "active",
                        "access_level": 20
                    }
                ],
                "groups": {},
                "projects": [3, 6]
            }
        ]

        mock_close_connection.return_value = None

        self.projects.set_user_groups(groups)

        listed_projects = [self.mock_projects.get_all_projects(
        )[0], self.mock_projects.get_all_projects()[1]]

        mongo = CongregateMongoConnector(client=mongomock.MongoClient)
        for project in listed_projects:
            self.projects.handle_retrieving_projects(False, project, mongo=mongo)

        actual_projects = [d for d, _ in mongo.stream_collection(
            "groups-bitbucket.company.com")]
        print(actual_projects)

        for i, _ in enumerate(expected_projects):
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())
