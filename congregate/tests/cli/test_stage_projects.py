import unittest
import mock
from congregate.cli import stage_projects
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.users import MockUsersApi
from congregate.helpers.configuration_validator import ConfigurationValidator


class StageProjectsTests(unittest.TestCase):
    def setUp(self):
        self.projects_api = MockProjectsApi()
        self.groups_api = MockGroupsApi()
        self.users_api = MockUsersApi()
        self.mock = mock.MagicMock()

    @mock.patch('__builtin__.open')
    @mock.patch('os.path.isfile')
    @mock.patch('congregate.cli.stage_projects.open_projects_file')
    @mock.patch('congregate.cli.stage_projects.open_users_file')
    @mock.patch('congregate.cli.stage_projects.open_groups_file')
    @mock.patch.object(ConfigurationValidator, 'dstn_parent_id', new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_type', new_callable=mock.PropertyMock)
    @mock.patch('congregate.cli.stage_projects.staged_users', [])
    @mock.patch('congregate.cli.stage_projects.staged_groups', [])
    @mock.patch('congregate.cli.stage_projects.staged_projects', [])
    def test_build_stage_data(self, mock_source_type, mock_parent_id, mock_groups, mock_users, mock_projects, mock_check, mock_open):
        mock_source_type.return_value = "gitlab"
        mock_parent_id.return_value = None
        mock_check.return_value = True
        mock_projects.return_value = self.projects_api.get_all_projects()
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
        mock_open.return_value = {}

        staged_projects, staged_users, staged_groups = stage_projects.build_staging_data([
                                                                                         "4", "6"])

        expected_projects = [
            {
                "name": "Diaspora Client",
                "path": "diaspora-client",
                "namespace": "diaspora",
                "members": [
                    {
                        "id": 2,
                        "username": "john_doe",
                        "name": "John Doe",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                        "web_url": "http://192.168.1.8:3000/root",
                        "expires_at": "2012-10-22T14:13:35Z",
                        "access_level": 30
                    }
                ],
                "http_url_to_repo": "http://example.com/diaspora/diaspora-client.git",
                "project_type": "group",
                "default_branch": "master",
                "visibility": "private",
                "id": 4,
                "description": "Project that does stuff",
                "shared_runners_enabled": True,
                "wiki_access_level": "enabled",
                "issues_access_level": "enabled",
                "merge_requests_access_level": "enabled",
                "builds_access_level": "enabled",
                "snippets_access_level": "disabled",
                "repository_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private",
                "path_with_namespace": "diaspora/diaspora-client",
                "archived": False,
                "shared_with_groups": []
            },
            {
                "name": "Puppet",
                "path": "puppet",
                "namespace": "brightbox",
                "members": [
                    {
                        "id": 2,
                        "username": "john_doe",
                        "name": "John Doe",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                        "web_url": "http://192.168.1.8:3000/root",
                        "expires_at": "2012-10-22T14:13:35Z",
                        "access_level": 30
                    }
                ],
                "default_branch": "master",
                "http_url_to_repo": "http://example.com/brightbox/puppet.git",
                "project_type": "group",
                "visibility": "private",
                "id": 6,
                "description": None,
                "shared_runners_enabled": True,
                "wiki_access_level": "enabled",
                "issues_access_level": "enabled",
                "merge_requests_access_level": "enabled",
                "builds_access_level": "enabled",
                "snippets_access_level": "disabled",
                "repository_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private",
                "path_with_namespace": "brightbox/puppet",
                "archived": False,
                "shared_with_groups": []
            }
        ]

        expected_users = [
            {
                "id": 2,
                "username": "john_doe",
                "name": "John Doe",
                "state": "active",
                "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                "web_url": "http://192.168.1.8:3000/root",
                "expires_at": "2012-10-22T14:13:35Z",
                "access_level": 30
            },
            {
                "username": "smart3",
                "web_url": "http://demo.tanuki.cloud/smart3",
                "name": "User smart3",
                "expires_at": None,
                "access_level": 50,
                "state": "active",
                "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                "id": 285
            },
            {
                "username": "smart4",
                "web_url": "http://demo.tanuki.cloud/smart4",
                "name": "User smart4",
                "expires_at": None,
                "access_level": 30,
                "state": "active",
                "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                "id": 286
            }
        ]

        expected_groups = [
            {
                "lfs_enabled": True,
                "request_access_enabled": False,
                "description": "An interesting group as well",
                "visibility": "public",
                "web_url": "http://localhost:3000/groups/foo-bar-2",
                "full_name": "Foobar Group 3",
                "path": "foo-bar-3",
                "id": 3,
                "name": "Foobar Group3",
                "members": [
                    {
                        "username": "smart3",
                        "access_level": 50,
                        "state": "active",
                        "web_url": "http://demo.tanuki.cloud/smart3",
                        "name": "User smart3",
                        "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                        "id": 285,
                        "expires_at": None
                    },
                    {
                        "username": "smart4",
                        "access_level": 30,
                        "state": "active",
                        "web_url": "http://demo.tanuki.cloud/smart4",
                        "name": "User smart4",
                        "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                        "id": 286,
                        "expires_at": None
                    }
                ],
                "parent_id": None,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "file_template_project_id": 1,
                "full_path": "foo-bar-3"
            },
            {
                "lfs_enabled": True,
                "request_access_enabled": False,
                "description": "An interesting group as well",
                "visibility": "public",
                "web_url": "http://localhost:3000/groups/foo-bar-2",
                "full_name": "Foobar Group 3",
                "path": "foo-bar-3",
                "id": 4,
                "name": "Foobar Group3",
                "members": [
                    {
                        "username": "smart3",
                        "access_level": 50,
                        "state": "active",
                        "web_url": "http://demo.tanuki.cloud/smart3",
                        "name": "User smart3",
                        "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                        "id": 285,
                        "expires_at": None
                    },
                    {
                        "username": "smart4",
                        "access_level": 30,
                        "state": "active",
                        "web_url": "http://demo.tanuki.cloud/smart4",
                        "name": "User smart4",
                        "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                        "id": 286,
                        "expires_at": None
                    }
                ],
                "parent_id": None,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "file_template_project_id": 1,
                "full_path": "foo-bar-3"
            }
        ]

        self.assertEqual(len(expected_projects), len(staged_projects))
        self.assertEqual(len(expected_groups), len(staged_groups))
        self.assertEqual(len(expected_users), len(staged_users))

        for i in range(len(expected_projects)):
            self.assertDictContainsSubset(
                expected_projects[i], staged_projects[i])
            self.assertItemsEqual(expected_projects[i], staged_projects[i])
        for i in range(len(expected_groups)):
            try:
                self.assertDictContainsSubset(
                    expected_groups[i], staged_groups[i])
                self.assertItemsEqual(expected_groups[i], staged_groups[i])
            except AssertionError:
                print("Expected: ", expected_groups[i])
                print("Staged: ", staged_groups[i])
                self.assertDictContainsSubset(
                    expected_groups[i], staged_groups[i])

        for i in range(len(expected_users)):
            self.assertDictContainsSubset(expected_users[i], staged_users[i])
            self.assertItemsEqual(expected_users[i], staged_users[i])

    @mock.patch('__builtin__.open')
    @mock.patch('os.path.isfile')
    @mock.patch('congregate.cli.stage_projects.open_projects_file')
    @mock.patch('congregate.cli.stage_projects.open_users_file')
    @mock.patch('congregate.cli.stage_projects.open_groups_file')
    @mock.patch.object(ConfigurationValidator, 'dstn_parent_id', new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_type', new_callable=mock.PropertyMock)
    @mock.patch('congregate.cli.stage_projects.staged_users', [])
    @mock.patch('congregate.cli.stage_projects.staged_groups', [])
    @mock.patch('congregate.cli.stage_projects.staged_projects', [])
    def test_build_stage_increment_no_parent_id(self, mock_source_type, mock_parent_id, mock_groups, mock_users, mock_projects, mock_check, mock_open):
        mock_source_type.return_value = "gitlab"
        mock_parent_id.return_value = None
        mock_check.return_value = True
        mock_projects.return_value = self.projects_api.get_all_projects()
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
        mock_open.return_value = {}

        staged_projects, staged_users, staged_groups = stage_projects.build_staging_data([
                                                                                         "1-2"])

        expected_projects = [
            {
                "name": "Diaspora Client",
                "path": "diaspora-client",
                "namespace": "diaspora",
                "members": [
                    {
                        "id": 2,
                        "username": "john_doe",
                        "name": "John Doe",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                        "web_url": "http://192.168.1.8:3000/root",
                        "expires_at": "2012-10-22T14:13:35Z",
                        "access_level": 30
                    }
                ],
                "http_url_to_repo": "http://example.com/diaspora/diaspora-client.git",
                "project_type": "group",
                "visibility": "private",
                "id": 4,
                "default_branch": "master",
                "description": "Project that does stuff",
                "shared_runners_enabled": True,
                "wiki_access_level": "enabled",
                "issues_access_level": "enabled",
                "merge_requests_access_level": "enabled",
                "builds_access_level": "enabled",
                "snippets_access_level": "disabled",
                "repository_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private",
                "path_with_namespace": "diaspora/diaspora-client",
                "archived": False,
                "shared_with_groups": []
            },
            {
                "name": "Puppet",
                "path": "puppet",
                "namespace": "brightbox",
                "members": [
                    {
                        "id": 2,
                        "username": "john_doe",
                        "name": "John Doe",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                        "web_url": "http://192.168.1.8:3000/root",
                        "expires_at": "2012-10-22T14:13:35Z",
                        "access_level": 30
                    }
                ],
                "http_url_to_repo": "http://example.com/brightbox/puppet.git",
                "project_type": "group",
                "visibility": "private",
                "id": 6,
                "default_branch": "master",
                "description": None,
                "shared_runners_enabled": True,
                "wiki_access_level": "enabled",
                "issues_access_level": "enabled",
                "merge_requests_access_level": "enabled",
                "builds_access_level": "enabled",
                "snippets_access_level": "disabled",
                "repository_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private",
                "path_with_namespace": "brightbox/puppet",
                "archived": False,
                "shared_with_groups": []
            }
        ]

        expected_users = [
            {
                "id": 2,
                "username": "john_doe",
                "name": "John Doe",
                "state": "active",
                "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                "web_url": "http://192.168.1.8:3000/root",
                "expires_at": "2012-10-22T14:13:35Z",
                "access_level": 30
            },
            {
                "username": "smart3",
                "web_url": "http://demo.tanuki.cloud/smart3",
                "name": "User smart3",
                "expires_at": None,
                "access_level": 50,
                "state": "active",
                "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                "id": 285
            },
            {
                "username": "smart4",
                "web_url": "http://demo.tanuki.cloud/smart4",
                "name": "User smart4",
                "expires_at": None,
                "access_level": 30,
                "state": "active",
                "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                "id": 286
            }
        ]

        expected_groups = [
            {
                "lfs_enabled": True,
                "request_access_enabled": False,
                "description": "An interesting group as well",
                "visibility": "public",
                "web_url": "http://localhost:3000/groups/foo-bar-2",
                "full_name": "Foobar Group 3",
                "path": "foo-bar-3",
                "id": 3,
                "name": "Foobar Group3",
                "members": [
                    {
                        "username": "smart3",
                        "access_level": 50,
                        "state": "active",
                        "web_url": "http://demo.tanuki.cloud/smart3",
                        "name": "User smart3",
                        "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                        "id": 285,
                        "expires_at": None
                    },
                    {
                        "username": "smart4",
                        "access_level": 30,
                        "state": "active",
                        "web_url": "http://demo.tanuki.cloud/smart4",
                        "name": "User smart4",
                        "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                        "id": 286,
                        "expires_at": None
                    }
                ],
                "parent_id": None,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "file_template_project_id": 1,
                "full_path": "foo-bar-3"
            },
            {
                "lfs_enabled": True,
                "request_access_enabled": False,
                "description": "An interesting group as well",
                "visibility": "public",
                "web_url": "http://localhost:3000/groups/foo-bar-2",
                "full_name": "Foobar Group 3",
                "path": "foo-bar-3",
                "id": 4,
                "name": "Foobar Group3",
                "members": [
                    {
                        "username": "smart3",
                        "access_level": 50,
                        "state": "active",
                        "web_url": "http://demo.tanuki.cloud/smart3",
                        "name": "User smart3",
                        "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                        "id": 285,
                        "expires_at": None
                    },
                    {
                        "username": "smart4",
                        "access_level": 30,
                        "state": "active",
                        "web_url": "http://demo.tanuki.cloud/smart4",
                        "name": "User smart4",
                        "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                        "id": 286,
                        "expires_at": None
                    }
                ],
                "parent_id": None,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "file_template_project_id": 1,
                "full_path": "foo-bar-3"
            }
        ]

        self.assertEqual(len(expected_projects), len(staged_projects))
        self.assertEqual(len(expected_groups), len(staged_groups))
        self.assertEqual(len(expected_users), len(staged_users))

        for i in range(len(expected_projects)):
            self.assertDictContainsSubset(
                expected_projects[i], staged_projects[i])
            self.assertItemsEqual(expected_projects[i], staged_projects[i])
        for i in range(len(expected_groups)):
            self.assertDictContainsSubset(expected_groups[i], staged_groups[i])
            self.assertItemsEqual(expected_groups[i], staged_groups[i])
        for i in range(len(expected_users)):
            self.assertDictContainsSubset(expected_users[i], staged_users[i])
            self.assertItemsEqual(expected_users[i], staged_users[i])

    @mock.patch('__builtin__.open')
    @mock.patch('os.path.isfile')
    @mock.patch('congregate.cli.stage_projects.open_projects_file')
    @mock.patch('congregate.cli.stage_projects.open_users_file')
    @mock.patch('congregate.cli.stage_projects.open_groups_file')
    @mock.patch.object(ConfigurationValidator, 'dstn_parent_id', new_callable=mock.PropertyMock)
    @mock.patch('congregate.cli.stage_projects.staged_users', [])
    @mock.patch('congregate.cli.stage_projects.staged_groups', [])
    @mock.patch('congregate.cli.stage_projects.staged_projects', [])
    def test_build_stage_data_all(self, parent_id, mock_groups, mock_users, mock_projects, mock_check, mock_open):
        parent_id.return_value = None
        mock_check.return_value = True
        mock_projects.return_value = self.projects_api.get_all_projects()
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
        mock_open.return_value = {}

        staged_projects, staged_users, staged_groups = stage_projects.build_staging_data([
                                                                                         "all"])

        self.assertEqual(
            len(self.projects_api.get_all_projects()), len(staged_projects))
        self.assertEqual(
            len(self.groups_api.get_all_groups_list()), len(staged_groups))
        self.assertEqual(
            len(self.users_api.get_all_users_list()), len(staged_users))

    @mock.patch('__builtin__.open')
    @mock.patch('os.path.isfile')
    @mock.patch('congregate.cli.stage_projects.open_projects_file')
    @mock.patch('congregate.cli.stage_projects.open_users_file')
    @mock.patch('congregate.cli.stage_projects.open_groups_file')
    @mock.patch.object(ConfigurationValidator, 'dstn_parent_id', new_callable=mock.PropertyMock)
    @mock.patch('congregate.cli.stage_projects.staged_users', [])
    @mock.patch('congregate.cli.stage_projects.staged_groups', [])
    @mock.patch('congregate.cli.stage_projects.staged_projects', [])
    def test_build_stage_data_none(self, parent_id, mock_groups, mock_users, mock_projects, mock_check, mock_open):
        parent_id.return_value = None
        mock_check.return_value = True
        mock_projects.return_value = self.projects_api.get_all_projects()
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
        mock_open.return_value = {}

        staged_projects, staged_users, staged_groups = stage_projects.build_staging_data([
            ""])

        self.assertEqual(len(staged_projects), 0)
        self.assertEqual(len(staged_groups), 0)
        self.assertEqual(len(staged_users), 0)
