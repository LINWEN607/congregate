import mock
import unittest
from cli import stage_projects
from helpers.mockapi.projects import MockProjectsApi
from helpers.mockapi.groups import MockGroupsApi
from helpers.mockapi.users import MockUsersApi
from helpers.mockapi.members import MockMembersApi
from helpers.base_module import app_path
from helpers.misc_utils import remove_dupes
import json

class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.projects_api = MockProjectsApi()
        self.groups_api = MockGroupsApi()
        self.users_api = MockUsersApi()
        self.members_api = MockMembersApi()
        self.mock = mock.MagicMock()
    
    @mock.patch('__builtin__.open')
    @mock.patch('os.path.isfile')
    @mock.patch('cli.stage_projects.open_projects_file')
    @mock.patch('cli.stage_projects.open_users_file')
    @mock.patch('cli.stage_projects.open_groups_file')
    @mock.patch('migration.gitlab.projects.ProjectsClient.get_members')
    def test_build_stage_data(self, mock_members, mock_groups, mock_users, mock_projects, mock_check, mock_open):
        mock_check.return_value = True
        mock_projects.return_value = self.projects_api.get_all_projects()
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
        mock_members.return_value = self.members_api.get_members_list()

        projects_to_stage = ["4", "6"]

        staged_projects, staged_users, staged_groups = stage_projects.build_staging_data(projects_to_stage)

        expected_projects = [
            {
                "name": "Diaspora Client", 
                "namespace": "diaspora", 
                "members": [
                    {
                        "username": "raymond_smith", 
                        "access_level": 30, 
                        "state": "active", 
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                        "web_url": "http://192.168.1.8:3000/root", 
                        "name": "Raymond Smith", 
                        "id": 1, 
                        "expires_at": "2012-10-22T14:13:35Z"
                    }, 
                    {
                        "username": "john_doe", 
                        "access_level": 30, 
                        "state": "active", 
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                        "web_url": "http://192.168.1.8:3000/root", 
                        "name": "John Doe", 
                        "id": 2, 
                        "expires_at": "2012-10-22T14:13:35Z"
                    }
                ], 
                "http_url_to_repo": "http://example.com/diaspora/diaspora-client.git", 
                "project_type": "group", 
                "visibilty": "private", 
                "id": 4
            }, 
            {
                "name": "Puppet", 
                "namespace": "brightbox", 
                "members": [
                    {
                        "username": "raymond_smith", 
                        "access_level": 30, 
                        "state": "active", 
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                        "web_url": "http://192.168.1.8:3000/root", 
                        "name": "Raymond Smith", 
                        "id": 1, 
                        "expires_at": "2012-10-22T14:13:35Z"
                    }, 
                    {
                        "username": "john_doe", 
                        "access_level": 30, 
                        "state": "active", 
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                        "web_url": "http://192.168.1.8:3000/root", 
                        "name": "John Doe", 
                        "id": 2, 
                        "expires_at": "2012-10-22T14:13:35Z"
                    }
                ], 
                "http_url_to_repo": "http://example.com/brightbox/puppet.git", 
                "project_type": "group", 
                "visibilty": "private", 
                "id": 6
            }
        ]

        expected_users = [
            {
                "username": "raymond_smith", 
                "access_level": 30, 
                "state": "active", 
                "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                "web_url": "http://192.168.1.8:3000/root", 
                "name": "Raymond Smith", 
                "id": 1, 
                "expires_at": "2012-10-22T14:13:35Z"
            }, 
            {
                "username": "john_doe", 
                "access_level": 30, 
                "state": "active", 
                "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                "web_url": "http://192.168.1.8:3000/root", 
                "name": "John Doe", 
                "id": 2, 
                "expires_at": "2012-10-22T14:13:35Z"
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
            },{
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

        self.assertEqual(expected_projects, staged_projects)
        self.assertEqual(expected_groups, staged_groups)
        self.assertEqual(expected_users, staged_users)

    
    @mock.patch('__builtin__.open')
    @mock.patch('os.path.isfile')
    @mock.patch('cli.stage_projects.open_projects_file')
    @mock.patch('cli.stage_projects.open_users_file')
    @mock.patch('cli.stage_projects.open_groups_file')
    @mock.patch('migration.gitlab.projects.ProjectsClient.get_members')
    def test_build_stage_increment(self, mock_members, mock_groups, mock_users, mock_projects, mock_check, mock_open):
        mock_check.return_value = True
        mock_projects.return_value = self.projects_api.get_all_projects()
        mock_users.return_value = self.users_api.get_all_users_list()
        mock_groups.return_value = self.groups_api.get_all_groups_list()
        mock_members.return_value = self.members_api.get_members_list()

        projects_to_stage = ["1-3"]

        staged_projects, staged_users, staged_groups = stage_projects.build_staging_data(projects_to_stage)

        expected_projects = [
            {
                "name": "Diaspora Client", 
                "namespace": "diaspora", 
                "members": [
                    {
                        "username": "raymond_smith", 
                        "access_level": 30, 
                        "state": "active", 
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                        "web_url": "http://192.168.1.8:3000/root", 
                        "name": "Raymond Smith", 
                        "id": 1, 
                        "expires_at": "2012-10-22T14:13:35Z"
                    }, 
                    {
                        "username": "john_doe", 
                        "access_level": 30, 
                        "state": "active", 
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                        "web_url": "http://192.168.1.8:3000/root", 
                        "name": "John Doe", 
                        "id": 2, 
                        "expires_at": "2012-10-22T14:13:35Z"
                    }
                ], 
                "http_url_to_repo": "http://example.com/diaspora/diaspora-client.git", 
                "project_type": "group", 
                "visibilty": "private", 
                "id": 4
            }, 
            {
                "name": "Puppet", 
                "namespace": "brightbox", 
                "members": [
                    {
                        "username": "raymond_smith", 
                        "access_level": 30, 
                        "state": "active", 
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                        "web_url": "http://192.168.1.8:3000/root", 
                        "name": "Raymond Smith", 
                        "id": 1, 
                        "expires_at": "2012-10-22T14:13:35Z"
                    }, 
                    {
                        "username": "john_doe", 
                        "access_level": 30, 
                        "state": "active", 
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                        "web_url": "http://192.168.1.8:3000/root", 
                        "name": "John Doe", 
                        "id": 2, 
                        "expires_at": "2012-10-22T14:13:35Z"
                    }
                ], 
                "http_url_to_repo": "http://example.com/brightbox/puppet.git", 
                "project_type": "group", 
                "visibilty": "private", 
                "id": 6
            },
                    {
                        "id": 80,
                        "description": None,
                        "default_branch": "master",
                        "visibility": "private",
                        "ssh_url_to_repo": "git@example.com:brightbox/puppet.git",
                        "http_url_to_repo": "http://example.com/brightbox/puppet.git",
                        "web_url": "http://example.com/brightbox/puppet",
                        "readme_url": "http://example.com/brightbox/puppet/blob/master/README.md",
                        "tag_list": [
                        "example",
                        "puppet"
                        ],
                        "owner": {
                        "id": 4,
                        "name": "Brightbox",
                        "created_at": "2013-09-30T13:46:02Z"
                        },
                        "name": "Puppet",
                        "name_with_namespace": "Brightbox / Puppet",
                        "path": "puppet",
                        "path_with_namespace": "brightbox/puppet",
                        "issues_enabled": True,
                        "open_issues_count": 1,
                        "merge_requests_enabled": True,
                        "jobs_enabled": True,
                        "wiki_enabled": True,
                        "snippets_enabled": False,
                        "resolve_outdated_diff_discussions": False,
                        "container_registry_enabled": False,
                        "created_at": "2013-09-30T13:46:02Z",
                        "last_activity_at": "2013-09-30T13:46:02Z",
                        "creator_id": 3,
                        "namespace": {
                        "id": 4,
                        "name": "Brightbox",
                        "path": "brightbox",
                        "kind": "group",
                        "full_path": "brightbox"
                        },
                        "import_status": "none",
                        "import_error": None,
                        "permissions": {
                        "project_access": {
                            "access_level": 10,
                            "notification_level": 3
                        },
                        "group_access": {
                            "access_level": 50,
                            "notification_level": 3
                        }
                        },
                        "archived": False,
                        "avatar_url": None,
                        "shared_runners_enabled": True,
                        "forks_count": 0,
                        "star_count": 0,
                        "runners_token": "b8547b1dc37721d05889db52fa2f02",
                        "public_jobs": True,
                        "shared_with_groups": [],
                        "only_allow_merge_if_pipeline_succeeds": False,
                        "only_allow_merge_if_all_discussions_are_resolved": False,
                        "request_access_enabled": False,
                        "merge_method": "merge",
                        "approvals_before_merge": 0,
                        "statistics": {
                        "commit_count": 12,
                        "storage_size": 2066080,
                        "repository_size": 2066080,
                        "lfs_objects_size": 0,
                        "job_artifacts_size": 0,
                        "packages_size": 0
                        },
                        "_links": {
                        "self": "http://example.com/api/v4/projects",
                        "issues": "http://example.com/api/v4/projects/1/issues",
                        "merge_requests": "http://example.com/api/v4/projects/1/merge_requests",
                        "repo_branches": "http://example.com/api/v4/projects/1/repository_branches",
                        "labels": "http://example.com/api/v4/projects/1/labels",
                        "events": "http://example.com/api/v4/projects/1/events",
                        "members": "http://example.com/api/v4/projects/1/members"
                        }
                    }
        ]

        expected_users = [
            {
                "username": "raymond_smith", 
                "access_level": 30, 
                "state": "active", 
                "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                "web_url": "http://192.168.1.8:3000/root", 
                "name": "Raymond Smith", 
                "id": 1, 
                "expires_at": "2012-10-22T14:13:35Z"
            }, 
            {
                "username": "john_doe", 
                "access_level": 30, 
                "state": "active", 
                "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon", 
                "web_url": "http://192.168.1.8:3000/root", 
                "name": "John Doe", 
                "id": 2, 
                "expires_at": "2012-10-22T14:13:35Z"
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
            }
        ]

        self.assertEqual(len(expected_projects), len(staged_projects))
        self.assertEqual(len(expected_groups), len(staged_groups))
        self.assertEqual(len(expected_users), len(staged_users))