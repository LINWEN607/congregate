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
from congregate.tests.mockapi.github.repos import MockReposApi
from congregate.tests.mockapi.github.headers import MockHeaders
from congregate.migration.github.repos import ReposClient
from congregate.migration.github.users import UsersClient
from congregate.migration.github.api.repos import ReposApi
from congregate.migration.gitlab.api.projects import ProjectsApi


@pytest.mark.unit_test
class ReposTests(unittest.TestCase):

    def setUp(self):
        self.mock_repos = MockReposApi()
        self.mock_headers = MockHeaders()
        self.repos = ReposClient(
            host="https://github.company.com", token="123")

    @patch.object(ReposApi, "get_repo")
    @patch.object(UsersClient, "format_users")
    @patch.object(ReposClient, "list_ci_sources_jenkins")
    @patch.object(ReposClient, "list_ci_sources_teamcity")
    @patch.object(MongoConnector, "close_connection")
    def test_format_user_repos(self,
                               mock_close_connection,
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

        mock_close_connection.return_value = None

        mongo = MongoConnector(
            host="test-server", port=123456, client=mongomock.MongoClient)
        for repo in listed_repos:
            self.repos.handle_retrieving_repos(repo, mongo=mongo)

        actual_projects = [d for d, _ in mongo.stream_collection(
            "projects-github.company.com")]

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
                "members": []
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
                "members": []
            }
        ]

        for i in range(len(expected_projects)):
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())

    @patch.object(ReposApi, "get_repo")
    @patch.object(UsersClient, "format_users")
    @patch.object(ReposClient, "list_ci_sources_jenkins")
    @patch.object(ReposClient, "list_ci_sources_teamcity")
    @patch.object(MongoConnector, "close_connection")
    def test_format_user_repos_with_error(self,
                                          mock_close_connection,
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

        mock_close_connection.return_value = None

        mongo = MongoConnector(
            host="test-server", port=123456, client=mongomock.MongoClient)
        for repo in listed_repos:
            self.repos.handle_retrieving_repos(repo, mongo=mongo)

        actual_projects = [d for d, _ in mongo.stream_collection(
            "projects-github.company.com")]

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
                "members": []
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

    @patch.object(ReposApi, "get_all_repo_collaborators")
    @patch.object(UsersClient, "format_users")
    @patch.object(ReposClient, "list_ci_sources_jenkins")
    @patch.object(ReposClient, "list_ci_sources_teamcity")
    @patch.object(MongoConnector, "close_connection")
    def test_format_org_repos(self,
                              mock_close_connection,
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

        mock_close_connection.return_value = None

        mongo = MongoConnector(
            host="test-server", port=123456, client=mongomock.MongoClient)
        for repo in listed_repos:
            self.repos.handle_retrieving_repos(repo, mongo=mongo)

        actual_projects = [d for d, _ in mongo.stream_collection(
            "projects-github.company.com")]

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

    @patch.object(ReposApi, "get_all_repo_collaborators")
    @patch.object(ReposClient, "list_ci_sources_jenkins")
    @patch.object(ReposClient, "list_ci_sources_teamcity")
    @patch.object(MongoConnector, "close_connection")
    def test_format_org_repos_no_members(self,
                                         mock_close_connection,
                                         mock_ci_sources1,
                                         mock_ci_sources2,
                                         mock_get_all_repo_collaborators
                                         ):

        mock_ci_sources1.return_value = []
        mock_ci_sources2.return_value = ['test-job1', 'test-job2']

        listed_repos = [self.mock_repos.get_listed_repos(
        )[2], self.mock_repos.get_listed_repos()[3]]

        mongo = MongoConnector(
            host="test-server", port=123456, client=mongomock.MongoClient)
        for repo in listed_repos:
            self.repos.handle_retrieving_repos(repo, mongo=mongo)

        actual_projects = [d for d, _ in mongo.stream_collection(
            "projects-github.company.com")]

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

    @patch("congregate.helpers.conf.Config.ci_sources")
    def test_list_ci_sources_jenkins(self, mock_ci_sources):
        mock_ci_sources.return_value = {
            "teamcity_ci_source": [
                {
                    "tc_ci_src_hostname": "tc_hostname",
                    "tc_ci_src_username": "test",
                    "tc_ci_src_access_token": "eyJ0eXA"
                }
            ],
            "jenkins_ci_source": [
                {
                    "jenkins_ci_src_hostname": "http://jenkins-test:8080",
                    "jenkins_ci_src_username": "jenkins-admin",
                    "jenkins_ci_src_access_token": "token"
                }
            ]
        }
        mongo_mock = MongoConnector(
            host="test-server", port=123456, client=mongomock.MongoClient)
        data = [
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
        ]

        for d in data:
            mongo_mock.insert_data('jenkins-test', d)

        expected = ["test-job1", "test-job2"]
        actual = self.repos.list_ci_sources_jenkins(
            "https://github.gitlab-proserv.net/gitlab/website.git", mongo_mock)

        self.assertListEqual(expected, actual)

    @patch("congregate.helpers.conf.Config.ci_sources")
    def test_list_ci_sources_teamcity(self, mock_ci_sources):
        mock_ci_sources.return_value = {
            "teamcity_ci_source": [
                {
                    "tc_ci_src_hostname": "tc_hostname",
                    "tc_ci_src_username": "test",
                    "tc_ci_src_access_token": "eyJ0eXA"
                }
            ],
            "jenkins_ci_source": [
                {
                    "jenkins_ci_src_hostname": "http://jenkins-test:8080",
                    "jenkins_ci_src_username": "jenkins-admin",
                    "jenkins_ci_src_access_token": "token"
                }
            ]
        }

        mongo_mock = MongoConnector(
            host="test-server", port=123456, client=mongomock.MongoClient)
        expected = []
        actual = self.repos.list_ci_sources_teamcity("website", mongo_mock)

        self.assertListEqual(expected, actual)

    @patch.object(ProjectsApi, "archive_project")
    @patch.object(ReposApi, "get_repo")
    def test_migrate_archived_repo_true(self, mock_get_repo, mock_archive):
        mock_repo = MagicMock()
        type(mock_repo).status_code = PropertyMock(return_value=200)
        mock_repo.json.return_value = self.mock_repos.get_repo()[0]
        mock_get_repo.return_value = mock_repo

        mock_archive = MagicMock()
        type(mock_archive).status_code = PropertyMock(return_value=200)

        repo = {
            "namespace": "test",
            "path": "path"
        }

        self.assertTrue(self.repos.migrate_archived_repo(1, repo))

    @patch.object(ReposApi, "get_repo")
    def test_migrate_archived_repo_false_not_archived(self, mock_get_repo):
        mock_repo = MagicMock()
        type(mock_repo).status_code = PropertyMock(return_value=200)
        mock_repo.json.return_value = self.mock_repos.get_repo()[1]
        mock_get_repo.return_value = mock_repo

        repo = {
            "namespace": "test",
            "path": "path"
        }

        self.assertFalse(self.repos.migrate_archived_repo(1, repo))

    @patch.object(ReposApi, "get_repo")
    def test_migrate_archived_repo_false_no_repo(self, mock_get_repo):
        mock_repo = MagicMock()
        type(mock_repo).status_code = PropertyMock(return_value=404)
        mock_repo.json.return_value = {
            "message": "Not Found",
            "documentation_url": "https://developer.github.com/enterprise/2.21/v3"
        }
        mock_get_repo.return_value = mock_repo

        repo = {
            "namespace": "test",
            "path": "path"
        }

        self.assertFalse(self.repos.migrate_archived_repo(1, repo))
