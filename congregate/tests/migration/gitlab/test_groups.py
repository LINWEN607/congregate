import unittest
import respx
import httpx
from unittest import mock
from pytest import mark

from gitlab_ps_utils.api import GitLabApi
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.gitlab.groups import GroupsClient
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.migration.gitlab.groups import GroupsApi
from congregate.migration.gitlab.users import UsersApi
from congregate.migration.meta.base_migrate import MigrateClient
from congregate.helpers.conf import Config
import congregate.helpers.migrate_utils as mig_utils


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
        self.migrate_client = MigrateClient()

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

    @respx.mock
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
        
        respx.get(url_value).mock(return_value=httpx.Response(
            status_code=200,
            json=self.mock_groups.get_group()
        ))
        
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
            {}
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

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.validate_dstn_token', return_value=True)
    @mock.patch.object(GroupsApi, 'share_group')
    @mock.patch.object(GroupsApi, 'get_group')
    @mock.patch.object(mig_utils, 'get_full_path_with_parent_namespace')
    @mock.patch.object(Config, 'destination_token', new_callable=mock.PropertyMock)
    @mock.patch.object(Config, 'destination_host', new_callable=mock.PropertyMock)
    def test_share_groups_with_groups_success(
        self, mock_dest_host, mock_dest_token, mock_get_full_path, mock_get_group, mock_share_group, mock_validate_token):
        mock_dest_host.return_value = "https://gitlabdestination.com"
        mock_dest_token.return_value = "destination_token"
        self.config = mock.Mock()
        self.config.source_host = "https://gitlabsource.com"
        self.config.source_token = "source_token"
        self.config.destination_host = "https://gitlabdestination.com"
        self.config.destination_token = "destination_token"
        self.groups_api = mock.Mock()
        self.migrate_client.groups_api = self.groups_api

        src_gid = 123
        dst_gid = 456
        shared_with_groups = [
            {
                'group_full_path': 'group1',
                'group_access_level': 40,
                'expires_at': None
            },
            {
                'group_full_path': 'group2',
                'group_access_level': 30,
                'expires_at': '2023-12-31'
            }
        ]

        # Mock get_group response
        mock_response_json = {'shared_with_groups': shared_with_groups}
        self.migrate_client.groups_api.get_group.return_value.json.return_value = mock_response_json

        # Mock get_full_path_with_parent_namespace
        with mock.patch.object(mig_utils, 'get_full_path_with_parent_namespace') as mock_get_full_path:
            mock_get_full_path.side_effect = lambda x: f"namespace/{x}"

            # Mock find_group_id_by_path directly on the instance
            self.migrate_client.groups.find_group_id_by_path = mock.Mock(side_effect=[1001, 1002])

            # Mock share_group response
            share_response_mock = mock.Mock()
            type(share_response_mock).status_code = mock.PropertyMock(return_value=201)
            self.migrate_client.groups_api.share_group.return_value = share_response_mock

            expected_result = {1001: True, 1002: True}

            actual_result = self.migrate_client.share_groups_with_groups(src_gid, dst_gid)

            self.assertEqual(expected_result, actual_result)
            self.assertEqual(self.migrate_client.groups_api.get_group.call_count, 1)
            self.assertEqual(self.migrate_client.groups.find_group_id_by_path.call_count, 2)
            self.assertEqual(self.migrate_client.groups_api.share_group.call_count, 2)

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.validate_dstn_token', return_value=True)
    @mock.patch.object(GroupsApi, 'share_group')
    @mock.patch.object(GroupsApi, 'get_group')
    @mock.patch.object(mig_utils, 'get_full_path_with_parent_namespace')
    @mock.patch.object(Config, 'destination_token', new_callable=mock.PropertyMock)
    @mock.patch.object(Config, 'destination_host', new_callable=mock.PropertyMock)
    def test_share_groups_with_groups_failure(
        self, mock_dest_host, mock_dest_token, mock_get_full_path, mock_get_group, mock_share_group, mock_validate_token):

        # Mock configuration properties
        mock_dest_host.return_value = "https://gitlabdestination.com"
        mock_dest_token.return_value = "destination_token"
        self.config = mock.Mock()
        self.config.source_host = "https://gitlabsource.com"
        self.config.source_token = "source_token"
        self.config.destination_host = "https://gitlabdestination.com"
        self.config.destination_token = "destination_token"
        self.groups_api = mock.Mock()
        self.migrate_client.groups_api = self.groups_api

        src_gid = 123
        dst_gid = 456
        shared_with_groups = [
            {
                'group_full_path': 'group1',
                'group_access_level': 40,
                'expires_at': None
            },
            {
                'group_full_path': 'group_missing',
                'group_access_level': 30,
                'expires_at': '2023-12-31'
            }
        ]

        # Mock get_group response
        mock_response_json = {'shared_with_groups': shared_with_groups}
        self.migrate_client.groups_api.get_group.return_value.json.return_value = mock_response_json

        # Mock get_full_path_with_parent_namespace
        with mock.patch.object(mig_utils, 'get_full_path_with_parent_namespace') as mock_get_full_path:
            mock_get_full_path.side_effect = lambda x: f"namespace/{x}"

            # Mock find_group_id_by_path to simulate missing group in destination
            # First group ID is found, second is None (missing)
            self.migrate_client.groups.find_group_id_by_path = mock.Mock(side_effect=[1001, None])

            # Mock share_group responses
            # First call succeeds, second call fails
            share_response_mock_success = mock.Mock()
            type(share_response_mock_success).status_code = mock.PropertyMock(return_value=201)

            share_response_mock_failure = mock.Mock()
            type(share_response_mock_failure).status_code = mock.PropertyMock(return_value=404)
            share_response_mock_failure.content = b'{"message": "Not Found"}'

            # Set side effect for share_group to return the success and failure responses
            self.migrate_client.groups_api.share_group.side_effect = [
                share_response_mock_success,
                share_response_mock_failure
            ]

            expected_result = {1001: True, None: False}

            actual_result = self.migrate_client.share_groups_with_groups(src_gid, dst_gid)

            self.assertEqual(expected_result, actual_result)
            self.assertEqual(self.migrate_client.groups_api.get_group.call_count, 1)
            self.assertEqual(self.migrate_client.groups.find_group_id_by_path.call_count, 2)
            self.assertEqual(self.migrate_client.groups_api.share_group.call_count, 2)
