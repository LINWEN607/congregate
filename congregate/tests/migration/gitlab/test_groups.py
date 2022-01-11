import unittest
import responses
from unittest import mock
from pytest import mark

from gitlab_ps_utils.api import GitLabApi
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.gitlab.groups import GroupsClient
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.migration.gitlab.groups import GroupsApi
from congregate.migration.gitlab.users import UsersApi


@mark.unit_test
class GroupsTests(unittest.TestCase):

    class MockReturn(object):
        status_code = None

        def __init__(self, json_in, status_code_in):
            self.json_string = json_in
            self.status_code = status_code_in

        def json(self):
            return self.json_string

    def setUp(self):
        self.mock_groups = MockGroupsApi()
        self.groups = GroupsClient()

    def test_is_group_non_empty_true(self):
        group = self.mock_groups.get_group()
        self.assertTrue(self.groups.is_group_non_empty(group))

    @mock.patch.object(ConfigurationValidator,
                       'destination_token', new_callable=mock.PropertyMock)
    @mock.patch.object(GitLabApi, "list_all")
    def test_is_group_non_empty_false_no_subgroups(
            self, mock_list_all, mock_token):
        mock_token.return_value = "test"
        group = self.mock_groups.get_group()
        group["projects"] = []
        mock_list_all.return_value = []
        self.assertFalse(self.groups.is_group_non_empty(group))

    # pylint: disable=no-member
    @responses.activate
    @mock.patch('congregate.helpers.conf.Config.destination_host',
                new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator,
                       'destination_token', new_callable=mock.PropertyMock)
    @mock.patch.object(GitLabApi, "list_all")
    @mock.patch.object(GitLabApi, "generate_get_request")
    def test_is_group_non_empty_true_subgroups(
            self, mock_get_group, mock_list_all, mock_token, mock_host):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        url_value = "https://gitlab.com/api/v4/groups"
        mock_list_all.return_value = [
            self.mock_groups.get_all_subgroups_list()[0]]
        responses.add(
            responses.GET,
            url_value,
            json=self.mock_groups.get_group(),
            status=200,
            content_type='text/json',
            match_querystring=True)
        group = self.mock_groups.get_group()
        group["projects"] = []
        self.assertTrue(self.groups.is_group_non_empty(group))

    @mock.patch("congregate.migration.gitlab.api.groups.GroupsApi.get_group_by_full_path")
    def test_find_group_id_by_path_returns_true_and_id_when_found(
            self, mock_get_group_by_full_path):
        mock_get_group_by_full_path.return_value = self.MockReturn({
                                                                   "id": 123}, 200)
        group_id = self.groups.find_group_id_by_path(
            "host", "token", "some_full_path")
        self.assertEqual(group_id, 123)

    @mock.patch("congregate.migration.gitlab.api.groups.GroupsApi.get_group_by_full_path")
    @mock.patch("congregate.migration.gitlab.api.namespaces.NamespacesApi.get_namespace_by_full_path")
    def test_find_group_id_by_path_calls_find_by_namespace_when_not_found_as_group(
            self, mock_get_namespace_by_full_path, mock_get_group_by_full_path):
        mock_get_group_by_full_path.return_value = self.MockReturn({
                                                                   "id": 123}, 500)
        mock_get_namespace_by_full_path.return_value = self.MockReturn({
                                                                       "id": 456}, 200)
        group_id = self.groups.find_group_id_by_path(
            "host", "token", "some_full_path")
        self.assertEqual(group_id, 456)

    @mock.patch("congregate.migration.gitlab.api.groups.GroupsApi.get_group_by_full_path")
    @mock.patch("congregate.migration.gitlab.api.namespaces.NamespacesApi.get_namespace_by_full_path")
    def test_find_group_id_by_path_returns_false_none_if_not_found(
            self, mock_get_namespace_by_full_path, mock_get_group_by_full_path):
        mock_get_group_by_full_path.return_value = self.MockReturn({
                                                                   "id": 123}, 500)
        mock_get_namespace_by_full_path.return_value = self.MockReturn({
                                                                       "id": 456}, 500)
        group_id = self.groups.find_group_id_by_path(
            "host", "token", "some_full_path")
        self.assertIsNone(group_id)

    @mock.patch('congregate.helpers.conf.Config.destination_host',
                new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator,
                       'destination_token', new_callable=mock.PropertyMock)
    @mock.patch.object(GroupsApi, "add_member_to_group")
    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_add_members_to_destination_group(
            self, user_search_mock, add_member_mock, mock_token, mock_host):
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
        actual = self.groups.add_members_to_destination_group(
            "", "", 000, members)
        self.assertDictEqual(expected, actual)

    @mock.patch('congregate.helpers.conf.Config.destination_host',
                new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator,
                       'destination_token', new_callable=mock.PropertyMock)
    @mock.patch.object(GroupsApi, "add_member_to_group")
    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_add_members_to_destination_group_missing_user(
            self, user_search_mock, add_member_mock, mock_token, mock_host):
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
        actual = self.groups.add_members_to_destination_group(
            "", "", 000, members)
        self.assertDictEqual(expected, actual)
