import unittest
import mock
import pytest

from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi
from congregate.tests.mockapi.gitlab.users import MockUsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.users import UsersApi


@pytest.mark.unit_test
class ProjectsTests(unittest.TestCase):
    def setUp(self):
        self.mock_groups = MockGroupsApi()
        self.mock_projects = MockProjectsApi()
        self.mock_users = MockUsersApi()
        self.groups_api = GroupsApi()
        self.projects_api = ProjectsApi()
        self.projects = ProjectsClient()

    @mock.patch("io.TextIOBase")
    @mock.patch('builtins.open')
    @mock.patch.object(ProjectsApi, "get_members")
    @mock.patch.object(GroupsApi, "get_all_group_projects")
    @mock.patch('congregate.helpers.conf.Config.src_parent_group_path', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.src_parent_id', new_callable=mock.PropertyMock)
    def test_retrieve_project_info_src_parent_group(self, mock_src_parent_id, mock_src_parent_group_path, mock_get_all_group_projects, mock_get_members, mock_open, mock_file):
        mock_src_parent_id.return_value = 42
        mock_src_parent_group_path.return_value = "mock_src_parent_group_path"
        mock_get_all_group_projects.return_value = self.mock_projects.get_all_projects()
        mock_get_members.return_value = self.mock_users.get_project_members()
        mock_open.return_value = mock_file
        self.assertEqual(self.projects.retrieve_project_info("host", "token").sort(
            key=lambda x: x["id"]), self.mock_projects.get_all_projects().sort(key=lambda x: x["id"]))

    @mock.patch("io.TextIOBase")
    @mock.patch('builtins.open')
    @mock.patch.object(ProjectsApi, "get_members")
    @mock.patch.object(ProjectsApi, "get_all_projects")
    @mock.patch('congregate.helpers.conf.Config.src_parent_group_path', new_callable=mock.PropertyMock)
    def test_retrieve_project_info(self, mock_src_parent_group_path, mock_get_all_projects, mock_get_members, mock_open, mock_file):
        mock_src_parent_group_path.return_value = None
        mock_get_all_projects.return_value = self.mock_projects.get_all_projects()
        mock_get_members.return_value = self.mock_users.get_project_members()
        mock_open.return_value = mock_file
        self.assertEqual(self.projects.retrieve_project_info("host", "token").sort(
            key=lambda x: x["id"]), self.mock_projects.get_all_projects().sort(key=lambda x: x["id"]))

    @mock.patch("io.TextIOBase")
    @mock.patch('builtins.open')
    @mock.patch.object(ProjectsApi, "get_all_projects")
    @mock.patch('congregate.helpers.conf.Config.src_parent_group_path', new_callable=mock.PropertyMock)
    def test_retrieve_project_info_error_message(self, mock_src_parent_group_path, mock_get_all_projects, mock_open, mock_file):
        mock_src_parent_group_path.return_value = None
        mock_get_all_projects.return_value = [{"message": "some error"}]
        mock_open.return_value = mock_file
        self.assertEqual(
            self.projects.retrieve_project_info("host", "token"), [])

    @mock.patch('congregate.helpers.conf.Config.destination_host', new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'destination_token', new_callable=mock.PropertyMock)
    @mock.patch.object(ProjectsApi, "add_member")
    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_add_members_to_destination_group(self, user_search_mock, add_member_mock, mock_token, mock_host):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
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
        user_search_mock.side_effect = [[user_data[0]], [user_data[1]]]
        member1_mock = mock.MagicMock()
        type(member1_mock).status_code = mock.PropertyMock(return_value=200)
        member1_mock.json.return_value = user_data[0]
        member2_mock = mock.MagicMock()
        type(member2_mock).status_code = mock.PropertyMock(return_value=200)
        member2_mock.json.return_value = user_data[1]
        add_member_mock.side_effect = [member1_mock, member2_mock]
        expected = {
            "johndoe@email.com": True,
            "janedoe@email.com": True
        }
        actual = self.projects.add_members_to_destination_project(
            "", "", 000, members)
        self.assertDictEqual(expected, actual)

    @mock.patch('congregate.helpers.conf.Config.destination_host', new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'destination_token', new_callable=mock.PropertyMock)
    @mock.patch.object(ProjectsApi, "add_member")
    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_add_members_to_destination_group_missing_user(self, user_search_mock, add_member_mock, mock_token, mock_host):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
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
        user_search_mock.side_effect = [[user_data[0]], [user_data[1]]]
        member1_mock = mock.MagicMock()
        type(member1_mock).status_code = mock.PropertyMock(return_value=200)
        member1_mock.json.return_value = user_data[0]
        member2_mock = mock.MagicMock()
        type(member2_mock).status_code = mock.PropertyMock(return_value=404)
        member2_mock.json.return_value = user_data[1]
        add_member_mock.return_value = member1_mock
        expected = {
            "johndoe@email.com": True,
            "janedoe@email.com": False
        }
        actual = self.projects.add_members_to_destination_project(
            "", "", 000, members)
        self.assertDictEqual(expected, actual)
