import unittest
from unittest.mock import patch, PropertyMock
from pytest import mark
from congregate.tests.mockapi.bitbucket.projects import MockProjectsApi
from congregate.migration.bitbucket.projects import ProjectsClient
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.tests.mockapi.bitbucket.groups import MockGroupsApi


@mark.unit_test
class ProjectsTests(unittest.TestCase):
    def setUp(self):
        self.mock_projects = MockProjectsApi()
        self.projects = ProjectsClient()
        self.mock_groups = MockGroupsApi()

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(ProjectsApi, "get_all_project_users")
    @patch.object(ProjectsApi, "get_all_project_repos")
    @patch.object(ProjectsApi, "get_all_projects")
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_retrieve_project_info(self, mock_ext_user_token, mock_ext_src_url, mock_get_all_projects, mock_get_all_project_repos, mock_get_all_project_users, mock_open, mock_file):
        mock_ext_src_url.return_value = "http://localhost:7990"
        mock_ext_user_token.return_value = "username:password"
        mock_get_all_project_repos.side_effect = [
            self.mock_projects.get_all_project_repos(), self.mock_projects.get_all_project_repos()]
        mock_get_all_project_users.side_effect = [
            self.mock_projects.get_all_project_users(), self.mock_projects.get_all_project_users()]
        mock_get_all_projects.return_value = self.mock_projects.get_all_projects()
        mock_open.return_value = mock_file
        expected_projects = [
            {
                "name": "test-group",
                "members": [
                    {
                        "username": "user2",
                        "name": "user2",
                        "access_level": 20,
                        "id": 3,
                        "email": "user2@example.com",
                        "state": "active",
                    }
                ],
                "path": "TGP",
                "full_path": "TGP",
                "projects": [
                    {
                        "path": "node",
                        "path_with_namespace": "TGP/node",
                        "namespace": {
                            "kind": "group",
                            "name": "test-group",
                            "path": "TGP",
                            "id": 1,
                            "full_path": "TGP"
                        },
                        "id": 3,
                        "name": "node",
                        "visibility": "private",
                        "description": ""
                    },
                    {
                        "path": "android",
                        "path_with_namespace": "TGP/android",
                        "namespace": {
                            "kind": "group",
                            "name": "test-group",
                            "path": "TGP",
                            "id": 1,
                            "full_path": "TGP"
                        },
                        "id": 6,
                        "name": "android",
                        "visibility": "private",
                        "description": "Android project"
                    }
                ],
                "id": 1,
                "visibility": "private",
                "description": "test"
            },
            {
                "name": "another-test-group",
                "members": [
                    {
                        "username": "user2",
                        "name": "user2",
                        "access_level": 20,
                        "id": 3,
                        "email": "user2@example.com",
                        "state": "active",
                    }
                ],
                "path": "ATP",
                "full_path": "ATP",
                "projects": [
                    {
                        "path": "node",
                        "path_with_namespace": "TGP/node",
                        "namespace": {
                            "kind": "group",
                            "name": "test-group",
                            "path": "TGP",
                            "id": 1,
                            "full_path": "TGP"
                        },
                        "id": 3,
                        "name": "node",
                        "visibility": "private",
                        "description": ""
                    },
                    {
                        "path": "android",
                        "path_with_namespace": "TGP/android",
                        "namespace": {
                            "kind": "group",
                            "name": "test-group",
                            "path": "TGP",
                            "id": 1,
                            "full_path": "TGP"
                        },
                        "id": 6,
                        "name": "android",
                        "visibility": "private",
                        "description": "Android project"
                    }
                ],
                "id": 2,
                "visibility": "private",
                "description": "test"
            }
        ]
        actual_projects = self.projects.retrieve_project_info()
        for i, _ in enumerate(expected_projects):
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(ProjectsApi, "get_all_project_groups")
    @patch.object(ProjectsApi, "get_all_project_users")
    @patch.object(ProjectsApi, "get_all_project_repos")
    @patch.object(ProjectsApi, "get_all_projects")
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_retrieve_project_info_with_groups(self, mock_ext_user_token, mock_ext_src_url, mock_get_all_projects, mock_get_all_project_repos, mock_get_all_project_users, mock_get_all_project_groups, mock_open, mock_file):
        mock_ext_src_url.return_value = "http://localhost:7990"
        mock_ext_user_token.return_value = "username:password"
        mock_get_all_project_repos.side_effect = [
            self.mock_projects.get_all_project_repos(), self.mock_projects.get_all_project_repos()]
        mock_get_all_project_users.side_effect = [
            self.mock_projects.get_all_project_users(), self.mock_projects.get_all_project_users()]
        mock_get_all_projects.return_value = self.mock_projects.get_all_projects()
        mock_get_all_project_groups.side_effect = [
            self.mock_projects.get_all_project_groups(), []]
        mock_open.return_value = mock_file
        groups = {
            "test-group": self.mock_groups.get_all_group_members()
        }
        expected_projects = [
            {
                "name": "test-group",
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
                "path": "TGP",
                "full_path": "TGP",
                "projects": [
                    {
                        "path": "node",
                        "path_with_namespace": "TGP/node",
                        "namespace": {
                            "kind": "group",
                            "name": "test-group",
                            "path": "TGP",
                            "id": 1,
                            "full_path": "TGP"
                        },
                        "id": 3,
                        "name": "node",
                        "visibility": "private",
                        "description": ""
                    },
                    {
                        "path": "android",
                        "path_with_namespace": "TGP/android",
                        "namespace": {
                            "kind": "group",
                            "name": "test-group",
                            "path": "TGP",
                            "id": 1,
                            "full_path": "TGP"
                        },
                        "id": 6,
                        "name": "android",
                        "visibility": "private",
                        "description": "Android project"
                    }
                ],
                "id": 1,
                "visibility": "private",
                "description": "test"
            },
            {
                "name": "another-test-group",
                "members": [
                    {
                        "username": "user2",
                        "name": "user2",
                        "access_level": 20,
                        "id": 3,
                        "email": "user2@example.com",
                        "state": "active",
                    }
                ],
                "path": "ATP",
                "full_path": "ATP",
                "projects": [
                    {
                        "path": "node",
                        "path_with_namespace": "TGP/node",
                        "namespace": {
                            "kind": "group",
                            "name": "test-group",
                            "path": "TGP",
                            "id": 1,
                            "full_path": "TGP"
                        },
                        "id": 3,
                        "name": "node",
                        "visibility": "private",
                        "description": ""
                    },
                    {
                        "path": "android",
                        "path_with_namespace": "TGP/android",
                        "namespace": {
                            "kind": "group",
                            "name": "test-group",
                            "path": "TGP",
                            "id": 1,
                            "full_path": "TGP"
                        },
                        "id": 6,
                        "name": "android",
                        "visibility": "private",
                        "description": "Android project"
                    }
                ],
                "id": 2,
                "visibility": "private",
                "description": "test"
            }
        ]

        actual_projects = self.projects.retrieve_project_info(groups=groups)
        for i, _ in enumerate(expected_projects):
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())
