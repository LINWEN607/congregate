import unittest
import mock
import responses

from congregate.migration.gitlab.groups import GroupsClient
from congregate.tests.mockapi.groups import MockGroupsApi


class GroupsUnitTest(unittest.TestCase):

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

    @mock.patch("congregate.migration.gitlab.groups.api.list_all")
    def test_is_group_non_empty_false_no_subgroups(self, mock_list_all):
        group = self.mock_groups.get_group()
        group["projects"] = []
        mock_list_all.return_value = []
        self.assertFalse(self.groups.is_group_non_empty(group))

    # pylint: disable=no-member
    @responses.activate
    @mock.patch("congregate.migration.gitlab.groups.api.list_all")
    @mock.patch("congregate.migration.gitlab.groups.api.generate_get_request")
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
    def test_find_group_by_path_returns_true_and_id_when_found(self, mock_get_group_by_full_path):
        mock_get_group_by_full_path.return_value = self.MockReturn({
                                                                   "id": 123}, 200)
        group_id = self.groups.find_group_by_path(
            "host", "token", "some_full_path")
        self.assertEqual(group_id, 123)

    @mock.patch("congregate.migration.gitlab.api.groups.GroupsApi.get_group_by_full_path")
    @mock.patch("congregate.migration.gitlab.api.namespaces.NamespacesApi.get_namespace_by_full_path")
    def test_find_group_by_path_calls_find_by_namespace_when_not_found_as_group(self, mock_get_namespace_by_full_path, mock_get_group_by_full_path):
        mock_get_group_by_full_path.return_value = self.MockReturn({
                                                                   "id": 123}, 500)
        mock_get_namespace_by_full_path.return_value = self.MockReturn({
                                                                       "id": 456}, 200)
        group_id = self.groups.find_group_by_path(
            "host", "token", "some_full_path")
        self.assertEqual(group_id, 456)

    @mock.patch("congregate.migration.gitlab.api.groups.GroupsApi.get_group_by_full_path")
    @mock.patch("congregate.migration.gitlab.api.namespaces.NamespacesApi.get_namespace_by_full_path")
    def test_find_group_by_path_returns_false_none_if_not_found(self, mock_get_namespace_by_full_path, mock_get_group_by_full_path):
        mock_get_group_by_full_path.return_value = self.MockReturn({
                                                                   "id": 123}, 500)
        mock_get_namespace_by_full_path.return_value = self.MockReturn({
                                                                       "id": 456}, 500)
        group_id = self.groups.find_group_by_path(
            "host", "token", "some_full_path")
        self.assertIsNone(group_id)
