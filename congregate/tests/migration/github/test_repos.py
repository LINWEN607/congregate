import unittest
from mock import patch, PropertyMock, MagicMock

from congregate.tests.mockapi.github.repos import MockReposApi
from congregate.migration.github.repos import ReposClient
from congregate.migration.github.users import UsersClient
from congregate.migration.github.api.repos import ReposApi


class ReposTests(unittest.TestCase):

    def setUp(self):
        self.mock_repos = MockReposApi()
        self.repos = ReposClient()

    @patch.object(ReposApi, "get_repo")
    @patch.object(UsersClient, "format_users")
    def test_format_user_repos(self,
                               mock_format_users,
                               mock_get_repo):
        formatted_users = [
            {
                "id": 3,
                "username": "gitlab",
                "name": "PS GitLab",
                "email": "proserv@gitlab.com",
                "avatar_url": "",
                "state": "active",
                "is_admin": True,
                "access_level": 40
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

        mock_format_users.side_effect = formatted_users

        mock_repo1 = MagicMock()
        type(mock_repo1).status_code = PropertyMock(return_value=200)
        mock_repo1.json.return_value = self.mock_repos.get_repo()[0]
        mock_repo2 = MagicMock()
        type(mock_repo2).status_code = PropertyMock(return_value=200)
        mock_repo2.json.return_value = self.mock_repos.get_repo()[1]
        mock_get_repo.side_effect = [mock_repo1, mock_repo2]

        listed_repos = [self.mock_repos.get_listed_repos(
        )[0], self.mock_repos.get_listed_repos()[1]]

        actual_projects = self.repos.format_repos([], listed_repos)

        expected_projects = [
            {
                "id": 1,
                "path": "website",
                "name": "website",
                "namespace": {
                    "id": 3,
                    "path": "gitlab",
                    "name": "gitlab",
                    "kind": "user",
                    "full_path": "gitlab"
                },
                "path_with_namespace": "gitlab/website",
                "visibility": "public",
                "description": None,
                "members": [formatted_users[0]]
            },
            {
                "id": 14,
                "path": "pprokic-public-repo",
                "name": "pprokic-public-repo",
                "namespace": {
                    "id": 6,
                    "path": "pprokic",
                    "name": "pprokic",
                    "kind": "user",
                    "full_path": "pprokic"
                },
                "path_with_namespace": "pprokic/pprokic-public-repo",
                "visibility": "public",
                "description": None,
                "members": [formatted_users[1]]
            }
        ]

        self.assertEqual(actual_projects.sort(
            key=lambda x: x["id"]), expected_projects.sort(key=lambda x: x["id"]))

    @patch.object(ReposApi, "get_repo")
    @patch.object(UsersClient, "format_users")
    def test_format_user_repos_with_error(self,
                                          mock_format_users,
                                          mock_get_repo):
        formatted_users = [
            {
                "id": 3,
                "username": "gitlab",
                "name": "PS GitLab",
                "email": "proserv@gitlab.com",
                "avatar_url": "",
                "state": "active",
                "is_admin": True,
                "access_level": 40
            }
        ]

        mock_format_users.return_value = formatted_users

        mock_repo1 = MagicMock()
        type(mock_repo1).status_code = PropertyMock(return_value=200)
        mock_repo1.json.return_value = self.mock_repos.get_repo()[0]
        mock_repo2 = MagicMock()
        type(mock_repo2).status_code = PropertyMock(return_value=404)
        json_404 = {
            "message": "Not Found",
            "documentation_url": "https://developer.github.com/enterprise/2.21/v3"
        }
        mock_repo2.json.return_value = json_404
        mock_get_repo.side_effect = [mock_repo1, mock_repo2]

        listed_repos = [self.mock_repos.get_listed_repos(
        )[0], self.mock_repos.get_listed_repos()[1]]

        actual_projects = self.repos.format_repos([], listed_repos)

        expected_projects = [
            {
                "id": 1,
                "path": "website",
                "name": "website",
                "namespace": {
                    "id": 3,
                    "path": "gitlab",
                    "name": "gitlab",
                    "kind": "user",
                    "full_path": "gitlab"
                },
                "path_with_namespace": "gitlab/website",
                "visibility": "public",
                "description": None,
                "members": formatted_users
            },
            {
                "id": 14,
                "path": "pprokic-public-repo",
                "name": "pprokic-public-repo",
                "namespace": {
                    "id": 6,
                    "path": "pprokic",
                    "name": "pprokic",
                    "kind": "user",
                    "full_path": "pprokic"
                },
                "path_with_namespace": "pprokic/pprokic-public-repo",
                "visibility": "public",
                "description": None,
                "members": []
            }
        ]

        self.assertLogs("Failed to get JSON for user {} repo {} ({})".format(
            "pprokic", "pprokic-public-repo", json_404))
        self.assertEqual(actual_projects.sort(
            key=lambda x: x["id"]), expected_projects.sort(key=lambda x: x["id"]))

    def test_format_user_repos_no_projects(self):
        listed_repos = [self.mock_repos.get_listed_repos(
        )[0], self.mock_repos.get_listed_repos()[1]]

        self.assertLogs("Failed to format repos {}".format(None))
        self.assertIsNone(self.repos.format_repos(None, listed_repos))
