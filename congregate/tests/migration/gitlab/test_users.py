import unittest
import json
import responses
import warnings
from unittest.mock import patch, mock_open, PropertyMock, MagicMock
from pytest import mark

from congregate.helpers.api import GitLabApi
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.migrate import MigrateClient
from congregate.tests.mockapi.gitlab.users import MockUsersApi
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.keys import KeysClient
from congregate.helpers.mdbc import MongoConnector
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
        actual = self.users.username_exists(old_user)
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
        actual = self.users.username_exists(old_user)
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
        actual = self.users.username_exists(old_user)
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
        actual = self.users.username_exists(old_user)
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
        old_user = {
            "email": "jdoe@email.com"
        }
        actual = self.users.user_email_exists(old_user)
        self.assertTrue(actual)

    @patch.object(UsersApi, "search_for_user_by_email")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_user_email_exists_false(self, dest_token, dest_host, search):
        search.return_value = [self.mock_users.get_dummy_user()]
        dest_host.return_value = "https//gitlab.example.com"
        dest_token.return_value = "token"
        old_user = {
            "email": "notjdoe@email.com"
        }
        actual = self.users.user_email_exists(old_user)
        self.assertFalse(actual)

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
        old_user = {
            "email": "notjdoe@email.com"
        }
        actual = self.users.user_email_exists(old_user)
        self.assertFalse(actual)

    @patch.object(UsersApi, "search_for_user_by_email")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    def test_user_email_exists_no_results(self, dest_token, dest_host, search):
        dest_host.return_value = "https//gitlab.example.com"
        dest_token.return_value = "token"
        old_user = {
            "email": "notjdoe@email.com"
        }
        search.return_value = []
        actual = self.users.user_email_exists(old_user)
        self.assertFalse(actual)

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
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d" % (
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
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d" % (
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
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d" % (
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
    @patch.object(GitLabApi, 'get_count')
    def test_block_user(self, count, dest_token, destination):
        destination.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        new_user = self.mock_users.get_dummy_user()

        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d" % (
            new_user["email"], count.return_value)
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=[self.mock_users.get_dummy_user()], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users/27/block"
        # pylint: disable=no-member
        responses.add(responses.POST, url_value,
                      json=self.mock_users.get_dummy_user_blocked(), status=201)

        self.assertEqual(self.users.block_user(new_user).status_code, 201)

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
        created_user_name = self.users.create_valid_username(dummy_user)
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
        created_user_name = self.users.create_valid_username(dummy_user)
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
        mock_username_suffix.return_value = "BLEPBLEP"
        dummy_user["username"] = "JUST NOW CREATED"
        created_user_name = self.users.create_valid_username(dummy_user)
        self.assertEqual(created_user_name,
                         dummy_user["username"] + "_BLEPBLEP")

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.username_suffix',
           new_callable=PropertyMock)
    @patch.object(UsersClient, "username_exists")
    @patch.object(UsersApi, "search_for_user_by_email")
    @patch.object(UsersClient, "user_email_exists")
    def test_create_valid_username_not_found_email_found_username_returns_unserscore_username_if_suffix_not_set(
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
        mock_username_suffix.return_value = None
        dummy_user["username"] = "JUST NOW CREATED"
        created_user_name = self.users.create_valid_username(dummy_user)
        self.assertEqual(created_user_name, dummy_user["username"] + "_")

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
    @patch.object(GroupsApi, "search_for_group")
    def test_is_username_group_path_not_found(
            self, group_api, dest_token, dest_host):
        group_api.return_value = [{"path": "xyz"}]
        dest_host.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        response = self.users.is_username_group_name({"username": "abc"})
        self.assertFalse(response)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(GroupsApi, "search_for_group")
    def test_is_username_group_path_found(
            self, group_api, dest_token, dest_host):
        group_api.return_value = [{"path": "abc"}]
        dest_host.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        response = self.users.is_username_group_name({"username": "abc"})
        self.assertTrue(response)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(GroupsApi, "search_for_group")
    def test_is_username_group_path_found_ignore_case(
            self, group_api, dest_token, dest_host):
        group_api.return_value = [{"path": "ABC"}]
        dest_host.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        response = self.users.is_username_group_name({"username": "abc"})
        self.assertTrue(response)

    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token',
                  new_callable=PropertyMock)
    @patch.object(GroupsApi, "search_for_group")
    def test_is_username_group_name_error_assumes_none(
            self, group_api, dest_token, dest_host):
        group_api.side_effect = Exception("THIS HAPPENED")
        dest_host.return_value = "https://gitlabdestination.com"
        dest_token.return_value = "token"
        response = self.users.is_username_group_name({"username": "abc"})
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
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d" % (
            new_user["email"], count.return_value)
        # pylint: disable=no-member
        responses.add(responses.GET, url_value, json=[], status=404)
        # pylint: enable=no-member

        expected = {
            "id": None,
            "email": "jdoe@email.com"
        }
        self.assertEqual(self.migrate.handle_user_creation(new_user), expected)

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(UsersApi, "get_all_users")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.projects_limit',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.src_parent_group_path',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    @patch.object(MongoConnector, "close_connection")
    def test_retrieve_user_info(self, close_connection, mock_sso, mock_src_parent_group_path,
                                mock_limit, mock_src_host, mock_dest_host, mock_get_all_users, mock_open, mock_file):
        mock_sso.return_value = ""
        mock_src_parent_group_path.return_value = ""
        mock_limit.return_value = None
        mock_src_host.return_value = "https://gitlab.example.com"
        mock_dest_host.return_value = "https://gitlab.com"
        close_connection.return_value = None
        mock_get_all_users.return_value = self.mock_users.get_test_source_users()
        mock_open.return_value = mock_file
        expected_users = [
            {
                "id": 28,
                "username": "raymond_smith",
                "name": "Raymond Smith",
                "state": "active",
                "avatar_url": "",
                "location": None,
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": None,
                "email": "rsmith@email.com",
                "theme_id": None,
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
                "location": None,
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": None,
                "email": "jdoe@email.com",
                "theme_id": None,
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
        mongo = MongoConnector(client=mongomock.MongoClient)
        for user in self.mock_users.get_test_source_users():
            self.users.handle_retrieving_users(user, mongo=mongo)
        actual_users = [d for d, _ in mongo.stream_collection(
            "users-gitlab.example.com")]

        self.assertGreater(len(actual_users), 0)

        for i, _ in enumerate(expected_users):
            self.assertDictEqual(expected_users[i], actual_users[i])

    @patch("io.TextIOBase")
    @patch('builtins.open')
    @patch.object(UsersApi, "get_user")
    @patch.object(GroupsApi, "get_all_group_members")
    @patch('congregate.helpers.conf.Config.destination_host',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.projects_limit',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.src_parent_group_path',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.src_parent_id',
           new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    @patch.object(MongoConnector, "close_connection")
    def test_retrieve_user_info_src_parent_group_sso(self, close_connection, mock_sso, mock_src_parent_id, mock_src_parent_group_path,
                                                     mock_limit, mock_src_host, mock_dest_host, mock_get_all_group_members, mock_get_user, mock_open, mock_file):
        mock_sso.return_value = "mock_sso"
        mock_src_parent_id.return_value = 42
        mock_limit.return_value = 100
        mock_src_host.return_value = "https://gitlab.example.com"
        mock_dest_host.return_value = "https://gitlab.example.com"
        mock_src_parent_group_path.return_value = "mock_src_parent_group_path"
        mock_get_all_group_members.return_value = self.mock_groups.get_group_members()
        mock_users = [
            self.mock_users.get_dummy_old_users()[0],
            self.mock_users.get_dummy_old_users()[1],
            self.mock_users.get_dummy_old_users()[1]
        ]
        ok_get_mock = MagicMock()
        type(ok_get_mock).status_code = PropertyMock(return_value=200)
        ok_get_mock.json.side_effect = mock_users
        close_connection.return_value = None
        mock_get_user.return_value = ok_get_mock
        mock_open.return_value = mock_file
        expected_users = [
            {
                "id": 3,
                "username": "raymond_smith",
                "name": "Raymond Smith",
                "state": "active",
                "location": None,
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": None,
                "email": "rsmith@email.com",
                "theme_id": None,
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
                "location": None,
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": None,
                "email": "jdoe@email.com",
                "theme_id": None,
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
        mongo = MongoConnector(client=mongomock.MongoClient)
        for user in mock_users:
            self.users.handle_retrieving_users(user, mongo=mongo)
        actual_users = [d for d, _ in mongo.stream_collection(
            "users-gitlab.example.com")]

        self.assertGreater(len(actual_users), 0)

        for i, _ in enumerate(expected_users):
            self.assertDictEqual(expected_users[i], actual_users[i])

    @patch('congregate.helpers.conf.Config.group_sso_provider_pattern',
           new_callable=PropertyMock)
    def test_generate_extern_uid(self, pattern):
        pattern.return_value = "email"
        mock_user = self.mock_users.get_dummy_user()
        expected = "jdoe@email.com"
        actual = self.users.generate_extern_uid(mock_user, None)

        self.assertEqual(expected, actual)

    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    def test_generate_extern_uid_no_pattern(self, provider):
        provider.return_value = "okta"
        mock_user = self.mock_users.get_dummy_user()
        mock_identity = mock_user.pop("identities")
        expected = "jdoe|someCompany|okta"
        actual = self.users.generate_extern_uid(mock_user, mock_identity)

        self.assertEqual(expected, actual)

    @patch('congregate.helpers.conf.Config.group_sso_provider',
           new_callable=PropertyMock)
    def test_generate_extern_uid_no_pattern_no_ids(self, provider):
        provider.return_value = "okta"
        mock_user = self.mock_users.get_dummy_user()
        expected = None
        actual = self.users.generate_extern_uid(mock_user, None)

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
        actual = self.users.generate_extern_uid(mock_user, None)

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
        valid_username.return_value = mock_user.get("username")
        extern_uid.return_value = mock_user.get("email")
        rand_pass.return_value = False
        reset_pass.return_value = True
        parent_id.return_value = 1234
        provider.return_value = "group_saml"
        expected = {
            "two_factor_enabled": False,
            "can_create_project": True,
            "twitter": "",
            "shared_runners_minutes_limit": None,
            "extern_uid": 'iwdewfsfdyyazqnpkwga@examplegitlab.com',
            "force_random_password": False,
            "group_id_for_saml": 1234,
            "linkedin": "",
            "color_scheme_id": 1,
            "skype": "",
            "is_admin": False,
            "id": 2,
            "projects_limit": 100000,
            "provider": "group_saml",
            "note": None,
            "state": "active",
            "reset_password": True,
            "location": None,
            "email": "iwdewfsfdyyazqnpkwga@examplegitlab.com",
            "website_url": "",
            "job_title": "",
            "username": "RzKciDiyEzvtSqEicsvW",
            "bio": None,
            "work_information": None,
            "private_profile": False,
            "external": False,
            "skip_confirmation": True,
            "organization": None,
            "public_email": "",
            "extra_shared_runners_minutes_limit": None,
            "name": "FrhUbyTGMoXQUTeaMgFW",
            "can_create_group": True,
            "avatar_url": "https://www.gravatar.com/avatar/a0290f87758efba7e7be1ed96b2e5ac1?s=80&d=identicon",
            "theme_id": 1
        }
        actual = self.users.generate_user_group_saml_post_data(mock_user)

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
    @patch('congregate.helpers.json_utils.read_json_file_into_object')
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
