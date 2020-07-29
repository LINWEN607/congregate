import unittest
import mock
from requests import Response

from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi
from congregate.tests.mockapi.gitlab.users import MockUsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.projects import ProjectsClient


class ProjectsTests(unittest.TestCase):
    def setUp(self):
        self.mock_groups = MockGroupsApi()
        self.mock_projects = MockProjectsApi()
        self.mock_users = MockUsersApi()
        self.groups_api = GroupsApi()
        self.projects_api = ProjectsApi()
        self.projects = ProjectsClient()

    @mock.patch("__builtin__.file")
    @mock.patch('__builtin__.open')
    @mock.patch.object(ProjectsApi, "get_members")
    @mock.patch.object(GroupsApi, "get_all_group_projects")
    @mock.patch('congregate.helpers.conf.Config.src_parent_group_path', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.src_parent_id', new_callable=mock.PropertyMock)
    def test_retrieve_project_info_src_parent_group(self, mock_src_parent_id, mock_src_parent_group_path, mock_get_all_group_projects, mock_get_members, mock_open, mock_file):
        self.maxDiff = None
        mock_src_parent_id.return_value = 42
        mock_src_parent_group_path.return_value = "mock_src_parent_group_path"
        mock_get_all_group_projects.return_value = self.mock_projects.get_all_projects()
        mock_get_members.return_value = self.mock_users.get_project_members()
        mock_open.return_value = mock_file
        self.assertEqual(sorted(self.projects.retrieve_project_info(
            "host", "token")), sorted(self.mock_projects.get_all_projects()))

    @mock.patch("__builtin__.file")
    @mock.patch('__builtin__.open')
    @mock.patch.object(ProjectsApi, "get_members")
    @mock.patch.object(ProjectsApi, "get_all_projects")
    @mock.patch('congregate.helpers.conf.Config.src_parent_group_path', new_callable=mock.PropertyMock)
    def test_retrieve_project_info(self, mock_src_parent_group_path, mock_get_all_projects, mock_get_members, mock_open, mock_file):
        mock_src_parent_group_path.return_value = None
        mock_get_all_projects.return_value = self.mock_projects.get_all_projects()
        mock_get_members.return_value = self.mock_users.get_project_members()
        mock_open.return_value = mock_file
        self.assertEqual(sorted(self.projects.retrieve_project_info(
            "host", "token")), sorted(self.mock_projects.get_all_projects()))

    @mock.patch("__builtin__.file")
    @mock.patch('__builtin__.open')
    @mock.patch.object(ProjectsApi, "get_all_projects")
    @mock.patch('congregate.helpers.conf.Config.src_parent_group_path', new_callable=mock.PropertyMock)
    def test_retrieve_project_info_error_message(self, mock_src_parent_group_path, mock_get_all_projects, mock_open, mock_file):
        mock_src_parent_group_path.return_value = None
        mock_get_all_projects.return_value = [{"message": "some error"}]
        mock_open.return_value = mock_file
        self.assertEqual(
            self.projects.retrieve_project_info("host", "token"), [])


    @mock.patch("requests.Response.json")
    @mock.patch("congregate.migration.gitlab.api.projects.ProjectsApi.add_member")
    @mock.patch("congregate.migration.gitlab.users.UsersClient.find_user_by_email_comparison_without_id")
    @mock.patch("congregate.helpers.misc_utils.safe_json_response")
    def test_add_members_to_destination_group(self, users, user_by_email, projects, resp):
        user_data = [
            {
                "email": "johndoe@email.com",
                "id": 1
            },
            {
                "email": "janedoe@email.com",
                "id": 2
            }
        ]
        members = [
            {
                "email": "johndoe@email.com"
            },
            {
                "email": "janedoe@email.com"
            }
        ]
        user_by_email.side_effect = user_data
        users.side_effect = [
            {
                "id": 1
            },
            {
                "id": 2
            }
        ]

        resp.json.side_effect = user_data

        projects.side_effect = [
            Response,
            Response
        ]

        expected = {
            "johndoe@email.com": True,
            "janedoe@email.com": True
        }

        actual = self.projects.add_members_to_destination_project("", "", 000, members)
        self.assertDictEqual(expected, actual)

    @mock.patch("requests.Response.json")
    @mock.patch("congregate.migration.gitlab.api.projects.ProjectsApi.add_member")
    @mock.patch("congregate.migration.gitlab.users.UsersClient.find_user_by_email_comparison_without_id")
    @mock.patch("congregate.helpers.misc_utils.safe_json_response")
    def test_add_members_to_destination_group_missing_user(self, users, user_by_email, projects, resp):
        user_data = [
            {
                "email": "johndoe@email.com",
                "id": 1
            },
            None
        ]
        members = [
            {
                "email": "johndoe@email.com"
            },
            {
                "email": "janedoe@email.com"
            }
        ]
        user_by_email.side_effect = user_data
        users.side_effect = [
            {
                "id": 1
            }
        ]

        resp.json.side_effect = user_data

        projects.side_effect = [
            Response
        ]

        expected = {
            "johndoe@email.com": True,
            "janedoe@email.com": False
        }

        actual = self.projects.add_members_to_destination_project("", "", 000, members)
        self.assertDictEqual(expected, actual)
