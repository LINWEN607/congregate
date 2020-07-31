import unittest
from mock import patch, PropertyMock

from congregate.tests.mockapi.bitbucket.projects import MockProjectsApi
from congregate.migration.bitbucket.projects import ProjectsClient
from congregate.migration.bitbucket.api.projects import ProjectsApi


class ProjectsTests(unittest.TestCase):
    def setUp(self):
        self.mock_projects = MockProjectsApi()
        self.projects = ProjectsClient()

    @patch("__builtin__.file")
    @patch('__builtin__.open')
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
                "name": "another-test-group",
                "members": [
                    {
                        "username": "user2",
                        "name": "user2",
                        "access_level": 20,
                        "id": 53,
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
            },
            {
                "name": "test-group",
                "members": [
                    {
                        "username": "user2",
                        "name": "user2",
                        "access_level": 20,
                        "id": 53,
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
            }
        ]
        self.assertEqual(
            sorted(self.projects.retrieve_project_info()), sorted(expected_projects))
