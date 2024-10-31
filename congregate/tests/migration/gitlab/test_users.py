import unittest
import json
import warnings
from unittest.mock import patch, mock_open, PropertyMock, MagicMock
import responses
from pytest import mark
from requests.exceptions import RequestException
from dacite import from_dict

from gitlab_ps_utils.api import GitLabApi

from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.meta.base_migrate import MigrateClient
from congregate.tests.mockapi.gitlab.users import MockUsersApi
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.namespaces import NamespacesApi
from congregate.migration.gitlab.keys import KeysClient
from congregate.helpers.congregate_mdbc import CongregateMongoConnector
from congregate.migration.meta.api_models.users import UserPayload
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock


@mark.unit_test
class UsersTests(unittest.TestCase):
    def setUp(self):
        self.mock_users = MockUsersApi()
        self.mock_groups = MockGroupsApi()
        self.users = UsersClient()
        self.migrate = MigrateClient(dry_run=False)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch('congregate.helpers.conf.Config.source_type',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'source_token',
                  new_callable=PropertyMock)
    @patch.object(GitLabApi, "generate_v4_request_url")
    def test_find_user_by_email_comparison_incorrect_user(
            self, url, src_token, src_host, src_type):
        url_value = "https://gitlabsource.com/api/v4/users/5"
        url.return_value = url_value
        src_token.return_value = "token"
        src_host.return_value = "https//gitlabsource.com"
        src_type.return_value = "gitlab"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_user_404(), status=404)
        # pylint: enable=no-member
        actual = self.users.find_user_by_email_comparison_with_id(5)
        self.assertIsNone(actual)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch('congregate.helpers.conf.Config.source_type',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'source_token',
                  new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(GitLabApi, "generate_v4_request_url")
    @patch.object(UsersApi, "search_for_user_by_email")
    def test_find_user_by_email_comparison_found_user(
            self, search, url, dest_token, dest_host, src_token, src_host, src_type):
        url_value = "https://gitlabsource.com/api/v4/users/5"
        url.return_value = url_value
        src_token.return_value = "token"
        src_host.return_value = "https//gitlabsource.com"
        src_type.return_value = "gitlab"
        dest_host.return_value = "https//gitlab.example.com"
        dest_token.return_value = "token"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        search.return_value = [self.mock_users.get_dummy_user()]
        actual = self.users.find_user_by_email_comparison_with_id(5)
        expected = self.mock_users.get_dummy_user()
        self.assertDictEqual(expected, actual)

    @patch.object(UsersClient, "is_username_group_name")
    @patch.object(UsersApi, "search_for_user_by_username")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_user_exists_true(
            self, dest_token, dest_host, search, users_client):
        users_client.return_value = False
        dest_host.return_value = "https//gitlab.example.com"
        dest_token.return_value = "token"
        search.return_value = [self.mock_users.get_dummy_user()]
        old_user = {
            "username": "jdoe"
        }
        actual = self.users.username_exists(old_user.get("username"), old_user)
        self.assertTrue(actual)

    @patch.object(UsersClient, "is_username_group_name")
    @patch.object(UsersApi, "search_for_user_by_username")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_user_exists_false(
            self, dest_token, dest_host, search, users_client):
        users_client.return_value = False
        dest_host.return_value = "https//gitlab.example.com"
        dest_token.return_value = "token"
        search.return_value = [self.mock_users.get_dummy_user()]
        old_user = {
            "username": "notjdoe"
        }
        actual = self.users.username_exists(old_user.get("username"), old_user)
        self.assertFalse(actual)

    @patch.object(UsersClient, "is_username_group_name")
    @patch.object(UsersApi, "search_for_user_by_username")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_user_exists_over_100(
            self, dest_token, dest_host, search, users_client):
        users_client.return_value = False
        dest_host.return_value = "https//gitlab.example.com"
        dest_token.return_value = "token"
        dummy_large_list = []
        for _ in range(0, 105):
            dummy_large_list.append(self.mock_users.get_dummy_user())
        search.return_value = dummy_large_list
        old_user = {
            "username": "notjdoe"
        }
        actual = self.users.username_exists(old_user.get("username"), old_user)
        self.assertFalse(actual)

    @patch.object(UsersClient, "is_username_group_name")
    @patch.object(UsersApi, "search_for_user_by_username")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_user_exists_no_results(
            self, dest_token, dest_host, search, users_client):
        users_client.return_value = False
        dest_host.return_value = "https//gitlab.example.com"
        dest_token.return_value = "token"
        old_user = {
            "username": "notjdoe"
        }
        search.return_value = []
        actual = self.users.username_exists(old_user.get("username"), old_user)
        self.assertFalse(actual)

    @patch.object(UsersApi, "search_for_user_by_email")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_user_email_exists_true(self, dest_token, dest_host, search):
        search.return_value = [self.mock_users.get_dummy_user()]
        dest_host.return_value = "https//gitlab.example.com"
        dest_token.return_value = "token"
        self.assertTrue(self.users.user_email_exists("jdoe@email.com"))

    @patch.object(UsersApi, "search_for_user_by_email")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_user_email_exists_false(self, dest_token, dest_host, search):
        search.return_value = [self.mock_users.get_dummy_user()]
        dest_host.return_value = "https//gitlab.example.com"
        dest_token.return_value = "token"
        self.assertFalse(self.users.user_email_exists("notjdoe@email.com"))

    @patch.object(UsersApi, "search_for_user_by_email")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_user_email_exists_over_100(self, dest_token, dest_host, search):
        dummy_large_list = []
        dest_host.return_value = "https//gitlab.example.com"
        dest_token.return_value = "token"
        for _ in range(0, 105):
            dummy_large_list.append(self.mock_users.get_dummy_user())
        search.return_value = dummy_large_list
        self.assertFalse(self.users.user_email_exists("notjdoe@email.com"))

    @patch.object(UsersApi, "search_for_user_by_email")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_user_email_exists_no_results(self, dest_token, dest_host, search):
        dest_host.return_value = "https//gitlab.example.com"
        dest_token.return_value = "token"
        search.return_value = []
        self.assertFalse(self.users.user_email_exists("notjdoe@email.com"))

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'dstn_parent_id',
                  new_callable=PropertyMock)
    @patch.object(GitLabApi, 'get_count')
    @patch.object(KeysClient, "migrate_user_ssh_keys")
    @patch.object(KeysClient, "migrate_user_gpg_keys")
    def test_handle_user_creation(
            self, get_gpg, get_ssh, count, parent_id, dest_token, destination):
        get_ssh.return_value = True
        get_gpg.return_value = True
        count.return_value = 1
        parent_id.return_value = None
        destination.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        new_user = self.mock_users.get_dummy_user()

        url_value = "https://gitlabdestination.com/api/v4/users"
        # pylint: disable=no-member
        responses.add(responses.POST, url_value,
                      json=self.mock_users.get_test_new_destination_users()[1], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=10&page=%d" % (
            new_user["email"], count.return_value)
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=[self.mock_users.get_dummy_user()], status=200)
        # pylint: enable=no-member

        expected = {
            "id": 27,
            "email": "jdoe@email.com"
        }
        self.assertEqual(self.migrate.handle_user_creation(new_user), expected)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'dstn_parent_id',
                  new_callable=PropertyMock)
    @patch.object(GitLabApi, 'get_count')
    @patch.object(KeysClient, "migrate_user_ssh_keys")
    @patch.object(KeysClient, "migrate_user_gpg_keys")
    def test_handle_user_creation_user_already_exists_no_parent_group(
            self, get_gpg, get_ssh, count, parent_id, dest_token, destination):
        get_ssh.return_value = True
        get_gpg.return_value = True
        count.return_value = 1
        parent_id.return_value = None
        destination.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        new_user = self.mock_users.get_dummy_user()

        url_value = "https://gitlabdestination.com/api/v4/users"
        # pylint: disable=no-member
        responses.add(responses.POST, url_value,
                      json=self.mock_users.get_test_new_destination_users()[1], status=409)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=10&page=%d" % (
            new_user["email"], count.return_value)
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=[self.mock_users.get_dummy_user()], status=200)
        # pylint: enable=no-member

        expected = {
            "id": 27,
            "email": "jdoe@email.com"
        }
        self.assertEqual(self.migrate.handle_user_creation(new_user), expected)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'dstn_parent_id',
                  new_callable=PropertyMock)
    @patch.object(GitLabApi, 'get_count')
    @patch.object(KeysClient, "migrate_user_ssh_keys")
    @patch.object(KeysClient, "migrate_user_gpg_keys")
    def test_handle_user_creation_user_already_exists_with_parent_group(
            self, get_gpg, get_ssh, count, parent_id, dest_token, destination):
        get_ssh.return_value = True
        get_gpg.return_value = True
        count.return_value = 1
        parent_id.return_value = 10
        destination.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        new_user = self.mock_users.get_dummy_user()

        url_value = "https://gitlabdestination.com/api/v4/users"
        # pylint: disable=no-member
        responses.add(responses.POST, url_value,
                      json=self.mock_users.get_test_new_destination_users()[1], status=409)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=10&page=%d" % (
            new_user["email"], count.return_value)
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=[self.mock_users.get_dummy_user()], status=200)
        # pylint: enable=no-member

        expected = {
            "id": 27,
            "email": "jdoe@email.com"
        }
        self.assertEqual(self.migrate.handle_user_creation(new_user), expected)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'source_token',
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'source_type',
                  new_callable=PropertyMock)
    @patch.object(UsersApi, "search_for_user_by_email")
    def test_block_user_no_user_match(self, mock_search, source_type, dest_token, src_token, dest_host):
        dest_host.side_effect = ["https://gitlabdestination.com",
                                 "https://gitlabdestination.com", "https://gitlabdestination.com"]
        src_token.side_effect = ["token", "token", "token"]
        dest_token.side_effect = ["token", "token", "token"]
        source_type.return_value = "gitlab"

        mock_search.return_value = []

        self.assertEqual(self.users.block_user(
            self.mock_users.get_dummy_user()), None)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'source_token',
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(UsersApi, "block_user")
    @patch.object(UsersApi, "search_for_user_by_email")
    def test_block_user_block_failed(self, mock_search, mock_block, dest_token, src_token, dest_host):
        dest_host.side_effect = ["https://gitlabdestination.com",
                                 "https://gitlabdestination.com", "https://gitlabdestination.com"]
        src_token.side_effect = ["token", "token", "token"]
        dest_token.side_effect = ["token", "token", "token"]

        mock_search.return_value = [self.mock_users.get_dummy_user()]

        user_block = MagicMock()
        type(user_block).status_code = PropertyMock(return_value=403)
        user_block.json.return_value = {"message": "Forbidden"}
        mock_block.return_value = user_block

        with self.assertLogs(self.users.log, level="ERROR"):
            self.assertEqual(self.users.block_user(
                self.mock_users.get_dummy_user()).status_code, 403)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'source_token',
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(UsersApi, "block_user")
    @patch.object(UsersApi, "search_for_user_by_email")
    def test_block_user_block_request_failed(self, mock_search, mock_block, dest_token, src_token, dest_host):
        dest_host.side_effect = ["https://gitlabdestination.com",
                                 "https://gitlabdestination.com", "https://gitlabdestination.com"]
        src_token.side_effect = ["token", "token", "token"]
        dest_token.side_effect = ["token", "token", "token"]

        mock_search.return_value = [self.mock_users.get_dummy_user()]

        mock_block.side_effect = RequestException()

        with self.assertLogs(self.users.log, level="ERROR"):
            self.assertEqual(self.users.block_user(
                self.mock_users.get_dummy_user()), None)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'source_token',
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(UsersApi, "modify_user")
    @patch.object(UsersApi, "block_user")
    @patch.object(UsersApi, "search_for_user_by_email")
    def test_block_user_admin_note(self, mock_search, mock_block, mock_modify, dest_token, src_token, dest_host):
        dest_host.side_effect = ["https://gitlabdestination.com",
                                 "https://gitlabdestination.com", "https://gitlabdestination.com"]
        src_token.side_effect = ["token", "token", "token"]
        dest_token.side_effect = ["token", "token", "token"]

        mock_search.return_value = [self.mock_users.get_dummy_user()]

        user_block = MagicMock()
        type(user_block).status_code = PropertyMock(return_value=201)
        user_block.json.return_value = self.mock_users.get_dummy_user_blocked()
        mock_block.return_value = user_block

        user_modify = MagicMock()
        type(user_modify).status_code = PropertyMock(return_value=200)
        user_modify.json.return_value = self.mock_users.get_dummy_user_blocked()
        mock_modify.return_value = user_modify

        self.assertEqual(self.users.block_user(
            self.mock_users.get_dummy_user()).status_code, 201)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'source_token',
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(UsersApi, "modify_user")
    @patch.object(UsersApi, "block_user")
    @patch.object(UsersApi, "search_for_user_by_email")
    def test_block_user_admin_note_request_failed(self, mock_search, mock_block, mock_modify, dest_token, src_token, dest_host):
        dest_host.side_effect = ["https://gitlabdestination.com",
                                 "https://gitlabdestination.com", "https://gitlabdestination.com"]
        src_token.side_effect = ["token", "token", "token"]
        dest_token.side_effect = ["token", "token", "token"]

        mock_search.return_value = [self.mock_users.get_dummy_user()]

        user_block = MagicMock()
        type(user_block).status_code = PropertyMock(return_value=201)
        user_block.json.return_value = self.mock_users.get_dummy_user_blocked()
        mock_block.return_value = user_block

        mock_modify.side_effect = RequestException()

        with self.assertLogs(self.users.log, level="ERROR"):
            self.assertEqual(self.users.block_user(
                self.mock_users.get_dummy_user()).status_code, 201)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'source_token',
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(UsersApi, "modify_user")
    @patch.object(UsersApi, "block_user")
    @patch.object(UsersApi, "search_for_user_by_email")
    def test_block_user_admin_note_failed(self, mock_search, mock_block, mock_modify, dest_token, src_token, dest_host):
        dest_host.side_effect = ["https://gitlabdestination.com",
                                 "https://gitlabdestination.com", "https://gitlabdestination.com"]
        src_token.side_effect = ["token", "token", "token"]
        dest_token.side_effect = ["token", "token", "token"]

        mock_search.return_value = [self.mock_users.get_dummy_user()]

        user_block = MagicMock()
        type(user_block).status_code = PropertyMock(return_value=201)
        user_block.json.return_value = self.mock_users.get_dummy_user_blocked()
        mock_block.return_value = user_block

        user_modify = MagicMock()
        type(user_modify).status_code = PropertyMock(return_value=409)
        user_modify.json.return_value = {"message": "Forbidden"}
        mock_modify.return_value = user_modify

        with self.assertLogs(self.users.log, level="ERROR"):
            self.assertEqual(self.users.block_user(
                self.mock_users.get_dummy_user()).status_code, 201)

    def test_remove_inactive_users(self):
        read_data = json.dumps(
            self.mock_users.get_test_new_destination_users())
        with patch('builtins.open', mock_open(read_data=read_data)):
            result = self.users.remove("staged_users")
        self.assertEqual(result, self.mock_users.get_dummy_new_users_active())

    def test_remove_inactive_users_project_members(self):
        read_data = json.dumps(self.mock_users.get_dummy_project())
        with patch('builtins.open', mock_open(read_data=read_data)):
            result = self.users.remove("staged_projects")
        self.assertEqual(
            result, self.mock_users.get_dummy_project_active_members())

    def test_remove_inactive_users_group_members(self):
        read_data = json.dumps(self.mock_groups.get_dummy_group())
        with patch('builtins.open', mock_open(read_data=read_data)):
            result = self.users.remove("staged_groups")
        self.assertEqual(
            result, self.mock_groups.get_dummy_group_active_members())

    def test_handle_users_not_found_users_keep(self):
        users_not_found = {
            28: "rsmith@email.com"
        }
        read_data = json.dumps(
            self.mock_users.get_test_new_destination_users())
        with patch('builtins.open', mock_open(read_data=read_data)):
            result = self.users.handle_users_not_found(
                "staged_users", users_not_found)
        self.assertEqual(result, self.mock_users.get_dummy_new_users_active())

    def test_handle_users_not_found_users(self):
        users_not_found = {
            27: "jdoe@email.com"
        }
        read_data = json.dumps(
            self.mock_users.get_test_new_destination_users())
        with patch('builtins.open', mock_open(read_data=read_data)):
            result = self.users.handle_users_not_found(
                "staged_users", users_not_found, keep=False)
        self.assertEqual(result, self.mock_users.get_dummy_new_users_active())

    def test_handle_users_not_found_groups(self):
        users_not_found = {
            87: "jdoe2@email.com",
            88: "jdoe3@email.com"
        }
        read_data = json.dumps(self.mock_groups.get_dummy_group())
        with patch('builtins.open', mock_open(read_data=read_data)):
            result = self.users.handle_users_not_found(
                "staged_groups", users_not_found)
        self.assertEqual(
            result, self.mock_groups.get_dummy_group_active_members())

    def test_handle_users_not_found_projects(self):
        users_not_found = {
            87: "jdoe2@email.com",
            88: "jdoe3@email.com"
        }
        read_data = json.dumps(self.mock_users.get_dummy_project())
        with patch('builtins.open', mock_open(read_data=read_data)):
            result = self.users.handle_users_not_found(
                "staged_projects", users_not_found)
        self.assertEqual(
            result, self.mock_users.get_dummy_project_active_members())

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(UsersApi, "search_for_user_by_email")
    @patch.object(UsersClient, "user_email_exists")
    def test_create_valid_username_found_email_returns_username(
            self, mock_email_check, mock_user_search, mock_token, mock_host):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        dummy_user = self.mock_users.get_dummy_user()
        mock_email_check.return_value = True
        mock_user_search.return_value = [dummy_user]
        created_user_name = self.users.create_valid_username(
            from_dict(data_class=UserPayload, data=dummy_user))
        self.assertEqual(created_user_name, dummy_user["username"])

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(UsersApi, "search_for_user_by_email")
    @patch.object(UsersClient, "user_email_exists")
    @patch.object(UsersClient, "username_exists")
    def test_create_valid_username_not_found_email_not_found_username_returns_passed_username(
            self,
            mock_username_exists,
            mock_email_check,
            mock_user_search,
            mock_token,
            mock_host):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        dummy_user = self.mock_users.get_dummy_user()
        mock_email_check.return_value = True
        mock_user_search.return_value = [dummy_user]
        mock_username_exists.return_value = False
        dummy_user["username"] = "JUST NOW CREATED"
        created_user_name = self.users.create_valid_username(
            from_dict(data_class=UserPayload, data=dummy_user))
        self.assertEqual(created_user_name, dummy_user["username"])

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.username_suffix',
           new_callable=PropertyMock)
    @patch.object(UsersClient, "username_exists")
    @patch.object(UsersApi, "search_for_user_by_email")
    @patch.object(UsersClient, "user_email_exists")
    def test_create_valid_username_not_found_email_found_username_returns_suffix_username_if_suffix_set(
            self,
            mock_email_check,
            mock_user_search,
            mock_username_exists,
            mock_username_suffix,
            mock_token,
            mock_host):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        dummy_user = self.mock_users.get_dummy_user()
        mock_email_check.return_value = False
        mock_user_search.return_value = [dummy_user]
        mock_username_exists.return_value = True
        mock_username_suffix.return_value = "___BLEPBLEP"
        dummy_user["username"] = "JUST NOW CREATED"
        created_user_name = self.users.create_valid_username(
            from_dict(data_class=UserPayload, data=dummy_user))
        self.assertEqual(created_user_name,
                         f"{dummy_user['username']}_BLEPBLEP")

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.username_suffix',
           new_callable=PropertyMock)
    @patch.object(UsersClient, "username_exists")
    @patch.object(UsersApi, "search_for_user_by_email")
    @patch.object(UsersClient, "user_email_exists")
    def test_create_valid_username_not_found_email_found_username_returns_username_if_suffix_not_set(
            self,
            mock_email_check,
            mock_user_search,
            mock_username_exists,
            mock_username_suffix,
            mock_token,
            mock_host):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        dummy_user = self.mock_users.get_dummy_user()
        mock_email_check.return_value = False
        mock_user_search.return_value = [dummy_user]
        mock_username_exists.return_value = True
        mock_username_suffix.return_value = "migrated"
        dummy_user["username"] = "JUST NOW CREATED"
        with self.assertLogs(self.users.log, level="WARNING"):
            created_user_name = self.users.create_valid_username(
                from_dict(data_class=UserPayload, data=dummy_user))
        self.assertEqual(created_user_name,
                         f"{dummy_user['username']}_migrated")

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch.object(GitLabApi, "generate_v4_request_url")
    @patch.object(UsersApi, "search_for_user_by_email")
    @patch('congregate.migration.gitlab.users.UsersClient.user_email_exists')
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_find_user_primarily_by_email_with_email(
            self, dest_token, dest_host, check, search, url):
        user = {
            "email": "jdoe@email.com",
            "id": 5
        }
        dest_host.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        url_value = "https://gitlabdestination.com/api/v4/users/5"
        url.return_value = url_value
        check.return_value = True
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        search.return_value = [self.mock_users.get_dummy_user()]
        actual = self.users.find_user_primarily_by_email(user)
        expected = self.mock_users.get_dummy_user()
        self.assertDictEqual(expected, actual)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch.object(GitLabApi, "generate_v4_request_url")
    @patch.object(UsersApi, "search_for_user_by_email")
    @patch('congregate.migration.gitlab.users.UsersClient.user_email_exists')
    @patch('congregate.helpers.conf.Config.source_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'source_token',
                  new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_find_user_primarily_by_email_with_id(
            self, dest_token, dest_host, src_token, src_host, check, search, url):
        user = {
            "id": 5
        }
        src_host.return_value = "https://gitlabsource.com"
        src_token.return_value = "token"
        dest_host.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        url_value = "https://gitlabsource.com/api/v4/users/5"
        url.return_value = url_value
        check.return_value = True
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        search.return_value = [self.mock_users.get_dummy_user()]
        actual = self.users.find_user_primarily_by_email(user)
        expected = self.mock_users.get_dummy_user()
        self.assertDictEqual(expected, actual)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch.object(GitLabApi, "generate_v4_request_url")
    @patch.object(UsersApi, "search_for_user_by_email")
    def test_find_user_primarily_by_email_with_invalid_object(
            self, search, url):
        user = {}
        url_value = "https://gitlabsource.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        search.return_value = [self.mock_users.get_dummy_user()]
        actual = self.users.find_user_primarily_by_email(user)
        self.assertIsNone(actual)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch.object(GitLabApi, "generate_v4_request_url")
    @patch.object(UsersApi, "search_for_user_by_email")
    def test_find_user_primarily_by_email_with_none(self, search, url):
        user = None
        url_value = "https://gitlabsource.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        search.return_value = [self.mock_users.get_dummy_user()]
        actual = self.users.find_user_primarily_by_email(user)
        self.assertIsNone(actual)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(NamespacesApi, "get_namespace_by_full_path")
    def test_is_username_group_path_not_found(
            self, namespace_api, dest_token, dest_host):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"kind": "group", "full_path": "subgroup/xyz"}
        namespace_api.return_value = mock_response
        dest_host.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        response = self.users.is_username_group_name(
            "abc", {"username": "abc"})
        self.assertFalse(response)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(NamespacesApi, "get_namespace_by_full_path")
    def test_is_username_group_path_found(
            self, namespace_api, dest_token, dest_host):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"kind": "group", "full_path": "abc"}
        namespace_api.return_value = mock_response
        dest_host.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        response = self.users.is_username_group_name(
            "abc", {"username": "abc"})
        self.assertTrue(response)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(NamespacesApi, "get_namespace_by_full_path")
    def test_is_username_group_path_found_ignore_case(
            self, namespace_api, dest_token, dest_host):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"kind": "group", "full_path": "ABC"}
        namespace_api.return_value = mock_response
        dest_host.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        response = self.users.is_username_group_name(
            "abc", {"username": "abc"})
        self.assertTrue(response)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(NamespacesApi, "get_namespace_by_full_path")
    def test_is_username_group_name_error_assumes_none(
            self, namespace_api, dest_token, dest_host):
        namespace_api.side_effect = RequestException("API call failed")
        dest_host.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        response = self.users.is_username_group_name(
            "abc", {"username": "abc"})
        self.assertIsNone(response)

    def test_get_user_creation_id_from_list(self):
        response = [{"id": 42, "email": "user1@example.com"},
                    {"id": 43, "email": "user2@example.com"}]
        self.assertEqual(
            self.users.get_user_creation_id_and_email(response), response[0])

    def test_get_user_creation_id_from_dict(self):
        response = {"id": 42, "email": "user1@example.com"}
        self.assertEqual(
            self.users.get_user_creation_id_and_email(response), response)

    def test_get_user_creation_id_invalid(self):
        response = []
        self.assertEqual(
            self.users.get_user_creation_id_and_email(response), None)
        response = None
        self.assertEqual(
            self.users.get_user_creation_id_and_email(response), None)
        response = {"name": "foo"}
        self.assertEqual(
            self.users.get_user_creation_id_and_email(response), None)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_type',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'dstn_parent_id',
                  new_callable=PropertyMock)
    @patch.object(GitLabApi, 'get_count')
    @patch.object(UsersClient, "generate_user_data")
    def test_handle_user_creation_improperly_formatted_json(
            self, mock_gen, count, parent_id, source_type, dest_token, destination):
        count.return_value = 1
        parent_id.return_value = None
        source_type.return_value = "gitlab"
        dest_token.return_value = "token"
        destination.return_value = "https://gitlabdestination.com"
        mock_gen.return_value = self.mock_users.get_user_gen()
        new_user = self.mock_users.get_dummy_user()

        # create_user
        url_value = "https://gitlabdestination.com/api/v4/users"
        # pylint: disable=no-member
        responses.add(responses.POST, url_value,
                      json=self.mock_users.get_user_400(), status=400)
        # pylint: enable=no-member

        # find_user_by_email_comparison_without_id
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=10&page=%d" % (
            new_user["email"], count.return_value)
        # pylint: disable=no-member
        responses.add(responses.GET, url_value, json=[], status=404)
        # pylint: enable=no-member

        expected = {
            "id": None,
            "email": "jdoe@email.com"
        }
        self.assertEqual(self.migrate.handle_user_creation(new_user), expected)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.projects_limit',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    @patch.object(CongregateMongoConnector, "close_connection")
    def test_retrieve_user_info(self, close_connection, mock_sso, mock_limit, mock_src_host, mock_dest_host):
        mock_sso.side_effect = ["", "", ""]
        mock_limit.side_effect = [None, None, None]
        mock_src_host.return_value = "https://gitlab.example.com"
        mock_dest_host.side_effect = [
            "https://gitlab.com", "https://gitlab.com", "https://gitlab.com"]
        close_connection.return_value = None
        expected_users = [
            {
                "id": 28,
                "username": "raymond_smith",
                "name": "Raymond Smith",
                "state": "active",
                "avatar_url": "",
                "location": "",
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": "",
                "email": "rsmith@email.com",
                "theme_id": 1,
                "color_scheme_id": 5,
                "identities": [],
                "can_create_group": True,
                "can_create_project": True,
                "two_factor_enabled": False,
                "external": False,
                "private_profile": None,
                "is_admin": False,
                "highest_role": 50,
                "shared_runners_minutes_limit": None,
                "extra_shared_runners_minutes_limit": None
            },
            {
                "id": 27,
                "name": "John Doe",
                "username": "jdoe",
                "state": "blocked",
                "avatar_url": "",
                "location": "",
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": "",
                "email": "jdoe@email.com",
                "theme_id": 1,
                "color_scheme_id": 5,
                "identities": [],
                "can_create_group": True,
                "can_create_project": True,
                "two_factor_enabled": False,
                "external": False,
                "private_profile": None,
                "is_admin": False,
                "highest_role": 50,
                "shared_runners_minutes_limit": None,
                "extra_shared_runners_minutes_limit": None
            }
        ]
        mongo = CongregateMongoConnector(client=mongomock.MongoClient)
        for user in self.mock_users.get_test_source_users():
            self.users.handle_retrieving_users(user, mongo=mongo)
        actual_users = [d for d, _ in mongo.stream_collection(
            "users-gitlab.example.com")]

        self.assertGreater(len(actual_users), 0)

        for i, j in enumerate(expected_users):
            self.assertDictEqual(j, actual_users[i])

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.projects_limit',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    @patch.object(CongregateMongoConnector, "close_connection")
    def test_retrieve_user_info_src_parent_group_sso(self, close_connection, mock_sso, mock_limit, mock_src_host, mock_dest_host):
        mock_sso.side_effect = ["mock_sso", "mock_sso", "mock_sso"]
        mock_limit.side_effect = [100, 100, 100]
        mock_src_host.return_value = "https://gitlab.example.com"
        mock_dest_host.side_effect = ["https://gitlab.example.com",
                                      "https://gitlab.example.com", "https://gitlab.example.com"]
        mock_users = [
            self.mock_users.get_dummy_old_users()[0],
            self.mock_users.get_dummy_old_users()[1],
            self.mock_users.get_dummy_old_users()[1]
        ]
        close_connection.return_value = None
        expected_users = [
            {
                "id": 3,
                "username": "raymond_smith",
                "name": "Raymond Smith",
                "state": "active",
                "location": "",
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": "",
                "email": "rsmith@email.com",
                "theme_id": 1,
                "color_scheme_id": 5,
                "projects_limit": 100,
                "identities": [],
                "can_create_group": True,
                "can_create_project": True,
                "two_factor_enabled": False,
                "external": False,
                "private_profile": None,
                "is_admin": False,
                "highest_role": 50,
                "shared_runners_minutes_limit": None,
                "extra_shared_runners_minutes_limit": None
            },
            {
                "id": 2,
                "name": "John Doe",
                "username": "jdoe",
                "state": "active",
                "location": "",
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": "",
                "email": "jdoe@email.com",
                "theme_id": 1,
                "color_scheme_id": 5,
                "projects_limit": 100,
                "identities": [],
                "can_create_group": True,
                "can_create_project": True,
                "two_factor_enabled": False,
                "external": False,
                "private_profile": None,
                "is_admin": False,
                "highest_role": 50,
                "shared_runners_minutes_limit": None,
                "extra_shared_runners_minutes_limit": None
            }
        ]
        mongo = CongregateMongoConnector(client=mongomock.MongoClient)
        for user in mock_users:
            self.users.handle_retrieving_users(user, mongo=mongo)
        actual_users = [d for d, _ in mongo.stream_collection(
            "users-gitlab.example.com")]

        self.assertGreater(len(actual_users), 0)

        for i, j in enumerate(expected_users):
            self.assertDictEqual(j, actual_users[i])

    @patch('congregate.helpers.conf.Config.group_sso_provider_pattern',
           new_callable=PropertyMock)
    def test_generate_extern_uid(self, pattern):
        pattern.return_value = "email"
        mock_user = self.mock_users.get_dummy_user()
        expected = "jdoe@email.com"
        actual = self.users.generate_extern_uid(
            from_dict(data_class=UserPayload, data=mock_user), None)
        self.assertEqual(expected, actual)

    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    def test_generate_extern_uid_no_pattern(self, provider):
        provider.return_value = "okta"
        mock_user = self.mock_users.get_dummy_user()
        mock_user_payload = from_dict(data_class=UserPayload, data=mock_user)
        mock_identity = mock_user.pop("identities")
        expected = "jdoe|someCompany|okta"
        actual = self.users.generate_extern_uid(
            mock_user_payload, mock_identity)
        self.assertEqual(expected, actual)

    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    def test_generate_extern_uid_no_pattern_no_ids(self, provider):
        provider.return_value = "okta"
        mock_user = self.mock_users.get_dummy_user()
        expected = None
        actual = self.users.generate_extern_uid(
            from_dict(data_class=UserPayload, data=mock_user), None)

        self.assertEqual(expected, actual)

    @patch('congregate.helpers.conf.Config.group_sso_provider_pattern',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.group_sso_provider_map_file',
           new_callable=PropertyMock)
    def test_generate_extern_uid_with_hash(self, map_file, pattern):
        pattern.return_value = "hash"
        map_file.return_value = "path/to/file"
        mock_user = self.mock_users.get_dummy_user()
        self.users.sso_hash_map = {
            "jdoe@email.com": {
                "email": "jdoe@email.com",
                "externalid": "abc123"
            },
            "mdoe@email.com": {
                "email": "mdoe@email.com",
                "externalid": "def456"
            }
        }

        expected = "abc123"
        actual = self.users.generate_extern_uid(
            from_dict(data_class=UserPayload, data=mock_user), None)

        self.assertEqual(expected, actual)

    def test_find_extern_uid_by_provider_no_identities(self):
        self.assertIsNone(self.users.find_extern_uid_by_provider(None, None))

    def test_find_extern_uid_by_provider_no_provider(self):
        identities = [
            {
                "provider": "okta",
                "extern_uid": "jdoe@email.com",
            }
        ]

        self.assertIsNone(
            self.users.find_extern_uid_by_provider(identities, None))

    def test_find_extern_uid_by_provider_with_provider(self):
        identities = [
            {
                "provider": "okta",
                "extern_uid": "jdoe@email.com",
            }
        ]

        expected = "jdoe@email.com"
        actual = self.users.find_extern_uid_by_provider(identities, "okta")

        self.assertEqual(expected, actual)

    @patch('congregate.helpers.conf.Config.reset_password',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.force_random_password',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    @patch('congregate.migration.gitlab.users.UsersClient.create_valid_username')
    def test_generate_user_data(self, valid_username, provider, rand_pass, reset_pass):
        mock_user = self.mock_users.get_dummy_staged_user()
        valid_username.return_value = mock_user.get("username")
        rand_pass.return_value = False
        reset_pass.return_value = True
        provider.return_value = None
        expected = {
            "two_factor_enabled": False,
            "can_create_project": True,
            "color_scheme_id": 1,
            "projects_limit": 100000,
            "bot": False,
            "private_profile": False,
            "state": "active",
            "email": "iwdewfsfdyyazqnpkwga@examplegitlab.com",
            "username": "RzKciDiyEzvtSqEicsvW",
            "external": False,
            "name": "FrhUbyTGMoXQUTeaMgFW",
            "can_create_group": True,
            "theme_id": 1,
            "commit_email": "iwdewfsfdyyazqnpkwga@examplegitlab.com",
            "skip_confirmation": True,
            "reset_password": True,
            "force_random_password": False,
            "using_license_seat": False
        }
        actual = self.users.generate_user_data(mock_user)
        print(actual)
        self.assertDictEqual(expected, actual)

    @patch.object(ConfigurationValidator, 'dstn_parent_id',
                  new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.reset_password',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.force_random_password',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    @patch('congregate.migration.gitlab.users.UsersClient.generate_extern_uid')
    @patch('congregate.migration.gitlab.users.UsersClient.create_valid_username')
    def test_generate_user_group_saml_post_data(
            self, valid_username, extern_uid, provider, rand_pass, reset_pass, parent_id):
        mock_user = self.mock_users.get_dummy_staged_user()
        mock_user["identities"] = [
            {
                "junk": "so it works"
            }
        ]
        valid_username.return_value = mock_user.get("username")
        extern_uid.return_value = mock_user.get("email")
        rand_pass.return_value = False
        reset_pass.return_value = True
        parent_id.return_value = 1234
        provider.return_value = "group_saml"
        expected = {
            "bot": False,
            "two_factor_enabled": False,
            "can_create_project": True,
            "extern_uid": 'iwdewfsfdyyazqnpkwga@examplegitlab.com',
            "group_id_for_saml": 1234,
            "color_scheme_id": 1,
            "projects_limit": 100000,
            "provider": "group_saml",
            "identities": [{"junk": "so it works"}],
            "state": "active",
            "email": "iwdewfsfdyyazqnpkwga@examplegitlab.com",
            "username": "RzKciDiyEzvtSqEicsvW",
            "private_profile": False,
            "external": False,
            "name": "FrhUbyTGMoXQUTeaMgFW",
            "can_create_group": True,
            "using_license_seat": False,
            "theme_id": 1
        }
        actual = self.users.generate_user_group_saml_post_data(
            from_dict(data_class=UserPayload, data=mock_user)).to_dict()
        print(actual)
        self.assertDictEqual(expected, actual)

    @patch.object(ConfigurationValidator, 'dstn_parent_id',
                  new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.reset_password',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.force_random_password',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    @patch('congregate.migration.gitlab.users.UsersClient.generate_extern_uid')
    @patch('congregate.migration.gitlab.users.UsersClient.create_valid_username')
    def test_generate_user_google_oauth_saml_post_data(
            self, valid_username, extern_uid, provider, rand_pass, reset_pass, parent_id):
        mock_user = self.mock_users.get_dummy_staged_user()
        mock_user["identities"] = [
            {
                "junk": "so it works"
            }
        ]
        valid_username.return_value = mock_user.get("username")
        extern_uid.return_value = "1234567890abcd"
        rand_pass.return_value = False
        reset_pass.return_value = True
        parent_id.return_value = 1234
        provider.return_value = "google_oauth2"
        expected = {
            "bot": False,
            "two_factor_enabled": False,
            "can_create_project": True,
            "color_scheme_id": 1,
            "projects_limit": 100000,
            "provider": "google_oauth2",
            "identities": [{"junk": "so it works"}],
            "state": "active",
            "email": "iwdewfsfdyyazqnpkwga@examplegitlab.com",
            "username": "RzKciDiyEzvtSqEicsvW",
            "private_profile": False,
            "external": False,
            "name": "FrhUbyTGMoXQUTeaMgFW",
            "can_create_group": True,
            "using_license_seat": False,
            "theme_id": 1,
            "extern_uid": '1234567890abcd'
        }
        actual = self.users.generate_user_group_saml_post_data(
            from_dict(data_class=UserPayload, data=mock_user)).to_dict()
        print(actual)
        self.assertDictEqual(expected, actual)

    @patch.object(ConfigurationValidator, 'dstn_parent_id',
                  new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.reset_password',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.force_random_password',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    @patch('congregate.migration.gitlab.users.UsersClient.generate_extern_uid')
    @patch('congregate.migration.gitlab.users.UsersClient.create_valid_username')
    def test_generate_user_saml_post_data_no_identities(
            self, valid_username, extern_uid, provider, rand_pass, reset_pass, parent_id):
        mock_user = self.mock_users.get_dummy_staged_user()
        mock_user["identities"] = []
        valid_username.return_value = mock_user.get("username")
        extern_uid.return_value = None
        rand_pass.return_value = False
        reset_pass.return_value = True
        parent_id.return_value = None
        provider.return_value = None
        expected = {
            "bot": False,
            "two_factor_enabled": False,
            "can_create_project": True,
            "color_scheme_id": 1,
            "projects_limit": 100000,
            "state": "active",
            "email": "iwdewfsfdyyazqnpkwga@examplegitlab.com",
            "username": "RzKciDiyEzvtSqEicsvW",
            "private_profile": False,
            "external": False,
            "name": "FrhUbyTGMoXQUTeaMgFW",
            "can_create_group": True,
            "using_license_seat": False,
            "theme_id": 1
        }
        actual = self.users.generate_user_group_saml_post_data(
            from_dict(data_class=UserPayload, data=mock_user)).to_dict()
        print(actual)
        self.assertDictEqual(expected, actual)

    @patch('congregate.helpers.conf.Config.group_sso_provider_pattern',
           new_callable=PropertyMock)
    def test_generate_hash_map_with_no_hash(self, pattern):
        pattern.return_value = "not hash"
        self.assertIsNone(self.users.generate_hash_map())

    @patch('congregate.helpers.conf.Config.group_sso_provider_pattern',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.group_sso_provider_map_file',
           new_callable=PropertyMock)
    @patch('gitlab_ps_utils.json_utils.read_json_file_into_object')
    def test_generate_hash_map_with_invalid_file(
            self, read_file, map_file, pattern):
        pattern.return_value = "hash"
        map_file.return_file = "path/to/file"
        read_file.side_effect = FileNotFoundError
        with self.assertRaises(SystemExit):
            self.users.generate_hash_map()

    @patch('congregate.helpers.conf.Config.group_sso_provider_pattern',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.group_sso_provider_map_file',
           new_callable=PropertyMock)
    def test_generate_hash_map_with_valid_file(self, map_file, pattern):
        pattern.return_value = "hash"
        map_file.return_value = "path/to/file"
        data = json.dumps([
            {
                "email": "jdoe@email.com",
                "externalid": "abc123"
            },
            {
                "email": "mdoe@email.com",
                "externalid": "def456"
            }
        ])
        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            expected = {
                "jdoe@email.com": {
                    "email": "jdoe@email.com",
                    "externalid": "abc123"
                },
                "mdoe@email.com": {
                    "email": "mdoe@email.com",
                    "externalid": "def456"
                }
            }

            actual = self.users.generate_hash_map()
            self.assertDictEqual(expected, actual)
