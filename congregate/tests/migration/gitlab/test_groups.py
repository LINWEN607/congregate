import unittest
import mock
import pytest
import responses

from requests import Response
from congregate.migration.gitlab.groups import GroupsClient
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi


@pytest.mark.unit_test
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

    @mock.patch("congregate.helpers.api.list_all")
    def test_is_group_non_empty_false_no_subgroups(self, mock_list_all):
        group = self.mock_groups.get_group()
        group["projects"] = []
        mock_list_all.return_value = []
        self.assertFalse(self.groups.is_group_non_empty(group))

    # pylint: disable=no-member
    @responses.activate
    @mock.patch("congregate.helpers.api.list_all")
    @mock.patch("congregate.helpers.api.generate_get_request")
    def test_is_group_non_empty_true_subgroups(self, mock_get_api, mock_list_all):
        url_value = "https://gitlab.com/api/v4/groups"
        mock_list_all.return_value = self.mock_groups.get_all_subgroups_list()
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
    def test_find_group_id_by_path_returns_true_and_id_when_found(self, mock_get_group_by_full_path):
        mock_get_group_by_full_path.return_value = self.MockReturn({
                                                                   "id": 123}, 200)
        group_id = self.groups.find_group_id_by_path(
            "host", "token", "some_full_path")
        self.assertEqual(group_id, 123)

    @mock.patch("congregate.migration.gitlab.api.groups.GroupsApi.get_group_by_full_path")
    @mock.patch("congregate.migration.gitlab.api.namespaces.NamespacesApi.get_namespace_by_full_path")
    def test_find_group_id_by_path_calls_find_by_namespace_when_not_found_as_group(self, mock_get_namespace_by_full_path, mock_get_group_by_full_path):
        mock_get_group_by_full_path.return_value = self.MockReturn({
                                                                   "id": 123}, 500)
        mock_get_namespace_by_full_path.return_value = self.MockReturn({
                                                                       "id": 456}, 200)
        group_id = self.groups.find_group_id_by_path(
            "host", "token", "some_full_path")
        self.assertEqual(group_id, 456)

    @mock.patch("congregate.migration.gitlab.api.groups.GroupsApi.get_group_by_full_path")
    @mock.patch("congregate.migration.gitlab.api.namespaces.NamespacesApi.get_namespace_by_full_path")
    def test_find_group_id_by_path_returns_false_none_if_not_found(self, mock_get_namespace_by_full_path, mock_get_group_by_full_path):
        mock_get_group_by_full_path.return_value = self.MockReturn({
                                                                   "id": 123}, 500)
        mock_get_namespace_by_full_path.return_value = self.MockReturn({
                                                                       "id": 456}, 500)
        group_id = self.groups.find_group_id_by_path(
            "host", "token", "some_full_path")
        self.assertIsNone(group_id)

    @mock.patch("requests.Response.json")
    @mock.patch("congregate.migration.gitlab.api.groups.GroupsApi.add_member_to_group")
    @mock.patch("congregate.migration.gitlab.users.UsersClient.find_user_by_email_comparison_without_id")
    @mock.patch("congregate.helpers.misc_utils.safe_json_response")
    def test_add_members_to_destination_group(self, users, user_by_email, groups, resp):
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

        groups.side_effect = [
            Response,
            Response
        ]

        expected = {
            "johndoe@email.com": True,
            "janedoe@email.com": True
        }

        actual = self.groups.add_members_to_destination_group("", "", 000, members)
        self.assertDictEqual(expected, actual)

    @mock.patch("requests.Response.json")
    @mock.patch("congregate.migration.gitlab.api.groups.GroupsApi.add_member_to_group")
    @mock.patch("congregate.migration.gitlab.users.UsersClient.find_user_by_email_comparison_without_id")
    @mock.patch("congregate.helpers.misc_utils.safe_json_response")
    def test_add_members_to_destination_group_missing_user(self, users, user_by_email, groups, resp):
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

        groups.side_effect = [
            Response
        ]

        expected = {
            "johndoe@email.com": True,
            "janedoe@email.com": False
        }

        actual = self.groups.add_members_to_destination_group("", "", 000, members)
        self.assertDictEqual(expected, actual)