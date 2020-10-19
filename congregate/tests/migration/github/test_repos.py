import unittest
import json
import pytest
from mock import patch, PropertyMock, MagicMock, mock_open
import warnings
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock
from congregate.helpers.mdbc import MongoConnector
from congregate.tests.mockapi.github.repos import MockReposApi
from congregate.migration.github.repos import ReposClient
from congregate.migration.github.users import UsersClient
from congregate.migration.github.api.repos import ReposApi
from congregate.helpers.conf import Config


@pytest.mark.unit_test
class ReposTests(unittest.TestCase):

    def setUp(self):
        self.mock_repos = MockReposApi()
        self.repos = self.mock_repo_client()

    @patch.object(ReposApi, "get_repo")
    @patch.object(UsersClient, "format_users")
    @patch.object(ReposClient, "list_ci_sources_jenkins")
    @patch.object(ReposClient, "list_ci_sources_teamcity")
    def test_format_user_repos(self,
                               mock_ci_sources1,
                               mock_ci_sources2,
                               mock_format_users,
                               mock_get_repo):
        
        mock_ci_sources1.return_value = []
        mock_ci_sources2.return_value = ['test-job1', 'test-job2']
        
        formatted_users1 = [
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

        formatted_users2 = [
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

        mock_format_users.side_effect = [formatted_users1, formatted_users2]

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
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
                "namespace": {
                    "id": 3,
                    "path": "gitlab",
                    "name": "gitlab",
                    "kind": "user",
                    "full_path": "gitlab"
                },
                "path_with_namespace": "gitlab/website",
                "http_url_to_repo": "https://github.gitlab-proserv.net/gitlab/website.git",
                "visibility": "public",
                "description": None,
                "members": formatted_users1
            },
            {
                "id": 14,
                "path": "pprokic-public-repo",
                "name": "pprokic-public-repo",
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
                "namespace": {
                    "id": 6,
                    "path": "pprokic",
                    "name": "pprokic",
                    "kind": "user",
                    "full_path": "pprokic"
                },
                "path_with_namespace": "pprokic/pprokic-public-repo",
                "http_url_to_repo": "https://github.gitlab-proserv.net/pprokic/pprokic-public-repo.git",
                "visibility": "public",
                "description": None,
                "members": formatted_users2
            }
        ]

        for i in range(len(expected_projects)):
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())


    @patch.object(ReposApi, "get_repo")
    @patch.object(UsersClient, "format_users")
    @patch.object(ReposClient, "list_ci_sources_jenkins")
    @patch.object(ReposClient, "list_ci_sources_teamcity")
    def test_format_user_repos_with_error(self,
                                        mock_ci_sources1,
                                        mock_ci_sources2,
                                        mock_format_users,
                                        mock_get_repo):
        
        mock_ci_sources1.return_value = []
        mock_ci_sources2.return_value = ['test-job1', 'test-job2']

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
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
                "namespace": {
                    "id": 3,
                    "path": "gitlab",
                    "name": "gitlab",
                    "kind": "user",
                    "full_path": "gitlab"
                },
                "http_url_to_repo": "https://github.gitlab-proserv.net/gitlab/website.git",
                "path_with_namespace": "gitlab/website",
                "visibility": "public",
                "description": None,
                "members": formatted_users
            },
            {
                "id": 14,
                "path": "pprokic-public-repo",
                "name": "pprokic-public-repo",
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
                "namespace": {
                    "id": 6,
                    "path": "pprokic",
                    "name": "pprokic",
                    "kind": "user",
                    "full_path": "pprokic"
                },
                "http_url_to_repo": "https://github.gitlab-proserv.net/pprokic/pprokic-public-repo.git",
                "path_with_namespace": "pprokic/pprokic-public-repo",
                "visibility": "public",
                "description": None,
                "members": []
            }
        ]

        self.assertLogs("Failed to get JSON for user {} repo {} ({})".format(
            "pprokic", "pprokic-public-repo", json_404))

        for i in range(len(expected_projects)):
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())

    def test_format_user_repos_no_projects(self):
        listed_repos = [self.mock_repos.get_listed_repos(
        )[0], self.mock_repos.get_listed_repos()[1]]

        self.assertLogs("Failed to format repos {}".format(None))
        self.assertIsNone(self.repos.format_repos(None, listed_repos))

    @patch.object(ReposApi, "get_all_repo_collaborators")
    @patch.object(UsersClient, "format_users")
    @patch.object(ReposClient, "list_ci_sources_jenkins")
    @patch.object(ReposClient, "list_ci_sources_teamcity")
    def test_format_org_repos(self,
                              mock_ci_sources1,
                              mock_ci_sources2,
                              mock_format_users,
                              mock_get_all_repo_collaborators):

        mock_ci_sources1.return_value = []
        mock_ci_sources2.return_value = ['test-job1', 'test-job2']

        formatted_users1 = [
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
                "id": 4,
                "username": "mlindsay",
                "name": None,
                "email": None,
                "avatar_url": "",
                "state": "active",
                "is_admin": True,
                "access_level": 40
            },
            {
                "id": 5,
                "username": "bmay",
                "name": None,
                "email": None,
                "avatar_url": "",
                "state": "active",
                "is_admin": False,
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

        formatted_users2 = [
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

        # [formatted_users1, formatted_users2]
        mock_format_users.side_effect = [[], []]

        mock_repo1 = MagicMock()
        type(mock_repo1).status_code = PropertyMock(return_value=200)
        mock_repo1.json.return_value = self.mock_repos.get_repo()[2]
        mock_repo2 = MagicMock()
        type(mock_repo2).status_code = PropertyMock(return_value=200)
        mock_repo2.json.return_value = self.mock_repos.get_repo()[3]
        mock_get_all_repo_collaborators.side_effect = [mock_repo1, mock_repo2]

        listed_repos = [self.mock_repos.get_listed_repos(
        )[2], self.mock_repos.get_listed_repos()[3]]

        actual_projects = self.repos.format_repos([], listed_repos)

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
                "members": [],  # formatted_users1
            },
            {
                "id": 16,
                "path": "test-repo",
                "name": "test-repo",
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
                "namespace": {
                    "id": 12,
                    "path": "org3",
                    "name": "org3",
                    "kind": "group",
                    "full_path": "org3"
                },
                "path_with_namespace": "org3/test-repo",
                "http_url_to_repo": "https://github.gitlab-proserv.net/org3/test-repo.git",
                "visibility": "public",
                "description": None,
                "members": [],  # formatted_users2
            }
        ]

        for i in range(len(expected_projects)):
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())

    @patch.object(ReposClient, "list_ci_sources_jenkins")
    @patch.object(ReposClient, "list_ci_sources_teamcity")
    def test_format_org_repos_no_members(self,
                                         mock_ci_sources1,
                                         mock_ci_sources2,
                                        ):
        
        mock_ci_sources1.return_value = []
        mock_ci_sources2.return_value = ['test-job1', 'test-job2']
        
        listed_repos = [self.mock_repos.get_listed_repos(
        )[2], self.mock_repos.get_listed_repos()[3]]

        actual_projects = self.repos.format_repos([], listed_repos, org=True)

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
                "members": []
            },
            {
                "id": 16,
                "path": "test-repo",
                "name": "test-repo",
                "ci_sources": {
                    "Jenkins": ['test-job1', 'test-job2'],
                    "TeamCity": []
                },
                "namespace": {
                    "id": 12,
                    "path": "org3",
                    "name": "org3",
                    "kind": "group",
                    "full_path": "org3"
                },
                "path_with_namespace": "org3/test-repo",
                "http_url_to_repo": "https://github.gitlab-proserv.net/org3/test-repo.git",
                "visibility": "public",
                "description": None,
                "members": []
            }
        ]

        for i in range(len(expected_projects)):
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())

    @patch("congregate.helpers.conf.Config.list_ci_source_config")
    def test_list_ci_sources_jenkins(self, list_ci_source_config):
        list_ci_source_config.return_value = [
            {
                "jenkins_ci_src_hostname": "http://jenkins-test:8080",
                "jenkins_ci_src_username": "jenkins-admin",
                "jenkins_ci_src_access_token": "token"
            }
        ]
        data = json.dumps([
            {
                "name": "demo-job",
                "url": "https://github.gitlab-proserv.net/firdaus/gitlab-jenkins.git"
            },
            {
                "name": "test-job1",
                "url": "https://github.gitlab-proserv.net/gitlab/website.git"
            },
            {
                "name": "test-job2",
                "url": "https://github.gitlab-proserv.net/gitlab/website.git"
            }   
        ])

        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            expected = ["test-job1","test-job2"]
            actual = self.repos.list_ci_sources_jenkins("website")

            self.assertListEqual(expected, actual)

    @patch.object(Config, "list_ci_source_config")
    def test_list_ci_sources_teamcity(self, mock_tc_ci_sources):
        mock_tc_ci_sources.return_value = [{
            "tc_ci_src_hostname": "tc_hostname",
            "tc_ci_src_username": "test",
            "tc_ci_src_access_token": "eyJ0eXA"
            }
        ]
        data = json.dumps([])

        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            expected = []
            actual = self.repos.list_ci_sources_teamcity("website")

            self.assertListEqual(expected, actual)
 
    def mock_repo_client(self):
        with patch.object(UsersClient, "connect_to_mongo") as mongo_mock:
            mongo_mock.return_value = MongoConnector(host="test-server", port=123456, client=mongomock.MongoClient)
            return ReposClient()