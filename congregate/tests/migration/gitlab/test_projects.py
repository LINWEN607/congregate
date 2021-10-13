import warnings
import unittest
from unittest.mock import patch, PropertyMock, MagicMock
from pytest import mark
from requests.exceptions import RequestException

from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi
from congregate.tests.mockapi.gitlab.users import MockUsersApi
from congregate.migration.gitlab.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.helpers.mdbc import MongoConnector
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock


@mark.unit_test
class ProjectsTests(unittest.TestCase):
    def setUp(self):
        self.mock_groups = MockGroupsApi()
        self.mock_projects = MockProjectsApi()
        self.mock_users = MockUsersApi()
        self.groups_api = GroupsApi()
        self.projects_api = ProjectsApi()
        self.projects = ProjectsClient()

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(ProjectsApi, "get_members")
    @patch.object(GroupsApi, "get_all_group_projects")
    @patch('congregate.helpers.conf.Config.src_parent_group_path', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.src_parent_id', new_callable=PropertyMock)
    @patch.object(MongoConnector, "close_connection")
    def test_retrieve_project_info_src_parent_group(self, mock_close, mock_src_parent_id, mock_src_parent_group_path, mock_get_all_group_projects, mock_get_members, mock_open, mock_file):
        mock_src_parent_id.return_value = 42
        mock_src_parent_group_path.return_value = "mock_src_parent_group_path"
        mock_get_all_group_projects.return_value = self.mock_projects.get_all_projects()
        mock_get_members.return_value = self.mock_users.get_project_members()
        mock_open.return_value = mock_file
        mock_close.return_value = None

        mongo = MongoConnector(client=mongomock.MongoClient)
        for project in self.groups_api.get_all_group_projects("https://gitlab.example.com", "token", 1):
            self.projects.handle_retrieving_project(
                "https://gitlab.example.com", "token", project, mongo=mongo)

        actual_projects = [d for d, _ in mongo.stream_collection(
            "projects-gitlab.example.com")]
        self.assertGreater(len(actual_projects), 0)
        expected_projects = self.mock_projects.get_all_projects()

        for i, _ in enumerate(expected_projects):
            self.assertDictEqual(expected_projects[i], actual_projects[i])

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(ProjectsApi, "get_members")
    @patch.object(ProjectsApi, "get_all_projects")
    @patch('congregate.helpers.conf.Config.src_parent_group_path', new_callable=PropertyMock)
    @patch.object(MongoConnector, "close_connection")
    def test_retrieve_project_info(self, mock_close, mock_src_parent_group_path, mock_get_all_projects, mock_get_members, mock_open, mock_file):
        mock_src_parent_group_path.return_value = None
        mock_get_all_projects.return_value = self.mock_projects.get_all_projects()
        mock_get_members.return_value = self.mock_users.get_project_members()
        mock_open.return_value = mock_file
        mock_close.return_value = None

        mongo = MongoConnector(client=mongomock.MongoClient)
        for project in self.projects_api.get_all_projects("https://gitlab.example.com", "token"):
            self.projects.handle_retrieving_project(
                "https://gitlab.example.com", "token", project, mongo=mongo)

        actual_projects = [d for d, _ in mongo.stream_collection(
            "projects-gitlab.example.com")]
        self.assertGreater(len(actual_projects), 0)
        expected_projects = self.mock_projects.get_all_projects()

        for i, _ in enumerate(expected_projects):
            self.assertDictEqual(expected_projects[i], actual_projects[i])

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(ProjectsApi, "get_all_projects")
    @patch('congregate.helpers.conf.Config.src_parent_group_path', new_callable=PropertyMock)
    @patch.object(MongoConnector, "close_connection")
    def test_retrieve_project_info_error_message(self, mock_close, mock_src_parent_group_path, mock_get_all_projects, mock_open, mock_file):
        mock_src_parent_group_path.return_value = None
        mock_get_all_projects.return_value = [{"message": "some error"}]
        mock_open.return_value = mock_file
        mock_close.return_value = None

        mongo = MongoConnector(client=mongomock.MongoClient)
        for project in self.projects_api.get_all_projects("https://gitlab.example.com", "token"):
            self.projects.handle_retrieving_project(
                "https://gitlab.example.com", "token", project, mongo=mongo)

        actual_projects = [d for d, _ in mongo.stream_collection(
            "gitlab.example.com-host")]
        self.assertEqual(len(actual_projects), 0)

    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token', new_callable=PropertyMock)
    @patch.object(ProjectsApi, "add_member")
    @patch.object(UsersApi, "search_for_user_by_email")
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
        member1_mock = MagicMock()
        type(member1_mock).status_code = PropertyMock(return_value=200)
        member1_mock.json.return_value = user_data[0]
        member2_mock = MagicMock()
        type(member2_mock).status_code = PropertyMock(return_value=200)
        member2_mock.json.return_value = user_data[1]
        add_member_mock.side_effect = [member1_mock, member2_mock]
        expected = {
            "johndoe@email.com": True,
            "janedoe@email.com": True
        }
        actual = self.projects.add_members_to_destination_project(
            "", "", 000, members)
        self.assertDictEqual(expected, actual)

    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token', new_callable=PropertyMock)
    @patch.object(ProjectsApi, "add_member")
    @patch.object(UsersApi, "search_for_user_by_email")
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
        member1_mock = MagicMock()
        type(member1_mock).status_code = PropertyMock(return_value=200)
        member1_mock.json.return_value = user_data[0]
        member2_mock = MagicMock()
        type(member2_mock).status_code = PropertyMock(return_value=404)
        member2_mock.json.return_value = user_data[1]
        add_member_mock.return_value = member1_mock
        expected = {
            "johndoe@email.com": True,
            "janedoe@email.com": False
        }
        actual = self.projects.add_members_to_destination_project(
            "", "", 000, members)
        self.assertDictEqual(expected, actual)

    def test_get_replacement_data(self):
        good_data = {
            "pattern": "some_pattern",
            "replace_with": "some_replacement"
        }
        f = ".gitlab-ci.yml"
        project_id = 1234
        src_branch = "a_branch"
        resp = self.projects.get_replacement_data(
            good_data, f, project_id, src_branch)
        self.assertEqual(resp[0], "some_pattern")
        self.assertEqual(resp[1], "some_replacement")

    def test_get_replacement_data_none_on_bad_data_elements(self):
        bad_data = {}
        f = ".gitlab-ci.yml"
        project_id = 1234
        src_branch = "a_branch"
        resp = self.projects.get_replacement_data(
            bad_data,
            f,
            project_id,
            src_branch
        )
        self.assertIsNone(resp)

        bad_data = {
            "data": {}
        }

        resp = self.projects.get_replacement_data(
            bad_data,
            f,
            project_id,
            src_branch
        )
        self.assertIsNone(resp)

        bad_data = {
            "data": {
                "pattern": ""
            }
        }

        resp = self.projects.get_replacement_data(
            bad_data,
            f,
            project_id,
            src_branch
        )
        self.assertIsNone(resp)

        bad_data = {
            "data": {
                "replace_with": ""
            }
        }

        resp = self.projects.get_replacement_data(
            bad_data,
            f,
            project_id,
            src_branch
        )
        self.assertIsNone(resp)

    @patch("congregate.helpers.migrate_utils.read_json_file_into_object")
    def test_filter_projects_by_state_archived(self, staged):
        staged.return_value = self.mock_projects.get_staged_projects()
        self.assertEqual(
            self.projects.filter_projects_by_state(archived=True), 1)

    @patch("congregate.helpers.migrate_utils.read_json_file_into_object")
    def test_filter_projects_by_state_unarchived(self, staged):
        staged.return_value = self.mock_projects.get_staged_projects()
        self.assertEqual(self.projects.filter_projects_by_state(), 2)

    @patch("congregate.helpers.migrate_utils.get_dst_path_with_namespace")
    @patch.object(ProjectsClient, "find_project_by_path")
    def test_find_mirror_project_double_false(self, mock_find_id, mock_get_path):
        mock_find_id.return_value = None
        mock_get_path.return_value = "pmm-demo/spring-app-secure-2"
        self.assertTupleEqual(self.projects.find_mirror_project(
            self.mock_projects.get_staged_group_project(), "host", "token", "namespace"), (False, False))

    @patch("congregate.helpers.migrate_utils.get_dst_path_with_namespace")
    @patch.object(ProjectsClient, "find_project_by_path")
    def test_find_mirror_project_false(self, mock_find_id, mock_get_path):
        mock_find_id.side_effect = [1, None]
        mock_get_path.side_effect = [
            "pmm-demo/spring-app-secure-2", "namespace/pmm-demo/spring-app-secure-2"]
        self.assertTupleEqual(self.projects.find_mirror_project(
            self.mock_projects.get_staged_group_project(), "host", "token", "namespace"), (1, False))

    @patch("congregate.helpers.migrate_utils.get_dst_path_with_namespace")
    @patch.object(ProjectsClient, "find_project_by_path")
    def test_find_mirror_project(self, mock_find_id, mock_get_path):
        mock_find_id.side_effect = [1, 2]
        mock_get_path.side_effect = [
            "pmm-demo/spring-app-secure-2", "namespace/pmm-demo/spring-app-secure-2"]
        self.assertTupleEqual(self.projects.find_mirror_project(
            self.mock_projects.get_staged_group_project(), "host", "token", "namespace"), (1, "namespace/pmm-demo/spring-app-secure-2"))

    @patch("congregate.helpers.migrate_utils.get_dst_path_with_namespace")
    @patch.object(ProjectsClient, "find_project_by_path")
    def test_find_mirror_project_exception(self, mock_find_id, mock_get_path):
        mock_get_path.return_value = "pmm-demo/spring-app-secure-2"
        mock_find_id.side_effect = RequestException()
        with self.assertLogs(self.projects.log, level="ERROR"):
            self.projects.find_mirror_project(
                self.mock_projects.get_staged_group_project(), "host", "token", "namespace")

    @patch.object(ProjectsClient, "find_mirror_project")
    @patch("congregate.helpers.migrate_utils.read_json_file_into_object")
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token', new_callable=PropertyMock)
    def test_push_mirror_staged_projects_fail(self, mock_token, mock_host, mock_staged, mock_find):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        mock_staged.return_value = self.mock_projects.get_staged_projects()
        mock_find.side_effect = [(False, False), (1, False), (2, False)]
        self.assertIsNone(
            self.projects.push_mirror_staged_projects("namespace"))

    @patch.object(ProjectsClient, "find_mirror_project")
    @patch("congregate.helpers.migrate_utils.read_json_file_into_object")
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token', new_callable=PropertyMock)
    def test_push_mirror_staged_projects(self, mock_token, mock_host, mock_staged, mock_find):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        mock_staged.return_value = self.mock_projects.get_staged_projects()
        mock_find.side_effect = [
            (False, False), (1, "namespace/test/path"), (2, False)]
        with self.assertLogs(self.projects.log, level="INFO"):
            self.projects.push_mirror_staged_projects("namespace")

    @patch.object(ProjectsClient, "find_mirror_project")
    @patch("congregate.helpers.migrate_utils.read_json_file_into_object")
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token', new_callable=PropertyMock)
    def test_toggle_staged_projects_push_mirror_fail(self, mock_token, mock_host, mock_staged, mock_find):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        mock_staged.return_value = self.mock_projects.get_staged_projects()
        mock_find.side_effect = [(False, False), (1, False), (2, False)]
        self.assertIsNone(
            self.projects.toggle_staged_projects_push_mirror("namespace"))
