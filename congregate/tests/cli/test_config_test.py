import unittest
import mock
from congregate.cli import config_test
from congregate.helpers.misc_utils import input_generator
from congregate.tests.mockapi.users import MockUsersApi
from congregate.tests.mockapi.groups import MockGroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi


test_dir_prefix = "./congregate/tests/cli/data/"


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.users_api = MockUsersApi()
        self.groups_api = MockGroupsApi()
        self.maxDiff = None


    @mock.patch.object(UsersApi, "get_current_user")
    def test_full_ext_src_skeleton(self, mock_get):
        """
            Generates a full skeleton outline of the configuration using empty strings and default values
            Compares that against the last known-good skeleton
        """
        values = [
            "hostname", # Destination hostname
            # "token", # Destination access token
            # "0",  # Destination import user id
            "True",   # shared runners enabled
            "False",  # append project suffix (retry)
            "disabled", # notification level
            "3",  # max_import_retries,
            "some_external_source", # external_src_url
            "username", # ext_src_user
            "repo_path", # ext_src_repo
            "False",    # keep_blocked_users
            "True",  # password reset email
            "False",    # randomized password
            "2",    # Threads
            "True", # strip namespace prefix
            "30"   # import wait time
        ]

        g = input_generator(values)

        mock_get.return_value = self.users_api.get_current_user()
        with mock.patch('congregate.cli.config_test.write_to_file', mock_file):
            with mock.patch('congregate.cli.config_test.app_path', "."):
                with mock.patch('congregate.cli.config_test.obfuscate', lambda x: "obfuscated==="):
                    with mock.patch('congregate.cli.config_test.deobfuscate', lambda x: "deobfuscated==="):
                        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
                            config_test.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_full_ext_src_skeleton.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)


    @mock.patch.object(GroupsApi, "get_group")
    @mock.patch.object(UsersApi, "get_current_user")
    def test_not_ext_src_parent_group_path_no_mirror_name_aws_skeleton(self, mock_get, mock_get_group):
        """
        Not external source
        parent group found (first if)
        No mirror (default)
        AWS (first if)
        """
        values = [
            "hostname", # Destination hostname
            # "token", # Destination access token
            # "0",  # Destination import user id
            "True",   # shared runners enabled
            "False",  # append project suffix (retry)
            "disabled", # notification level
            "3",  # max_import_retries,
            "gitlab", # external_src_url
            "source_hostname", # source host
            # "source_access_token", # source token
            "source_registry_url",    # source registry url
            "3600", # max_export_wait_time
            "destination_registry_url",    # destination registry url
            "0",  # destination parent group id
            # "parent_group_path",  # destination parent group full path
            # "True",  # privatize_groups
            "group_sso_provider",  # SSO provider
            "username_suffix",  # username suffix
            "No",   # mirror
            # "mirror_username",  # mirror username
            "aws",  # export location
            "s3_name",  # bucket name
            "us-east-1",    # bucket region
            # "access key",   # access key
            # "secret key",   # secret key
            "absolute_path",    # file system path
            "False",    # keep_blocked_users
            "True",  # password reset email
            "False",    # randomized password
            "2",    # Threads
            "True", # strip namespace prefix
            "30"   # import wait time
        ]

        g = input_generator(values)

        mock_get.return_value = self.users_api.get_current_user()

        class Hack(object):
            def __init__(self):
                self._json = {"full_path": "destination_group_full_path"}
            def json(self):
                return self._json

        mock_get_group.return_value = Hack()
        with mock.patch('congregate.cli.config_test.write_to_file', mock_file):
            with mock.patch('congregate.cli.config_test.getcwd', lambda : "."):
                with mock.patch('congregate.cli.config_test.get_congregate_path', lambda : "."):
                    with mock.patch('congregate.cli.config_test.obfuscate', lambda x: "obfuscated==="):
                        with mock.patch('congregate.cli.config_test.deobfuscate', lambda x: "deobfuscated==="):
                            with mock.patch('__builtin__.raw_input', lambda x: next(g)):
                                config_test.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_parent_group_path_no_mirror_name_aws_skeleton.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)


    @mock.patch.object(GroupsApi, "get_group")
    @mock.patch.object(UsersApi, "get_current_user")
    def test_not_ext_src_no_parent_group_path_mirror_name_filesystem_skeleton(self, mock_get_current_user, mock_get_group):
        """
        Not external source
        no parent group
        mirror
        filesystem
        """
        values = [
            "hostname", # Destination hostname
            # "token", # Destination access token
            # "0",  # Destination import user id
            "True",   # shared runners enabled
            "False",  # append project suffix (retry)
            "disabled", # notification level
            "3",  # max_import_retries,
            "gitlab", # external_src_url
            "source_hostname", # source host
            # "source_access_token", # source token
            "source_registry_url",    # source registry url
            "3600", # max_export_wait_time
            "destination_registry_url",    # destination registry url
            "0",  # destination parent group id
            # "parent_group_path",  # destination parent group full path
            # "True",  # privatize_groups
            "group_sso_provider",  # SSO provider
            "username_suffix",  # username suffix
            "Yes",   # mirror
            # "mirror_username",  # mirror username
            "filesystem",  # export location
            # "s3_name",  # bucket name
            # "us-east-1",    # bucket region
            # "access key",   # access key
            # "secret key",   # secret key
            "absolute_path",    # file system path
            "False",    # keep_blocked_users
            "True",  # password reset email
            "False",    # randomized password
            "2",    # Threads
            "True", # strip namespace prefix
            "30"   # import wait time
        ]

        g = input_generator(values)

        mock_get_current_user.return_value = {"id": 123, "username": "username"}

        class GroupHack(object):
            def __init__(self):
                self._json = {"full_path": None}
            def json(self):
                return self._json

        mock_get_group.return_value = GroupHack()

        with mock.patch('congregate.cli.config_test.write_to_file', mock_file):
            with mock.patch('congregate.cli.config_test.getcwd', lambda : "."):
                with mock.patch('congregate.cli.config_test.get_congregate_path', lambda : "."):
                    with mock.patch('congregate.cli.config_test.obfuscate', lambda x: "obfuscated==="):
                        with mock.patch('congregate.cli.config_test.deobfuscate', lambda x: "deobfuscated==="):
                            with mock.patch('__builtin__.raw_input', lambda x: next(g)):
                                config_test.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_no_parent_group_path_mirror_name_filesystem_skeleton.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)


    def test_update_config_with_changes(self):
        data = '{\
            "dstn_hostname":"hostname",\
            "dstn_access_token":"obfuscated===",\
            "import_user_id":"1",\
            "shared_runners_enabled":"False",\
            "project_suffix":"False",\
            "notification_level":"disabled",\
            "max_import_retries":"3",\
            "dstn_registry_url":"destination_registry_url",\
            "parent_group_id":"1",\
            "parent_group_path":"destination_group_full_path",\
            "privatize_groups":"True",\
            "group_sso_provider":"",\
            "username_suffix":"local",\
            "mirror_username":"",\
            "src_hostname":"source_hostname",\
            "src_access_token":"obfuscated===",\
            "src_registry_url":"source_registry_url",\
            "max_export_wait_time":"3600",\
            "location":"aws",\
            "s3_name":"s3_name",\
            "s3_region":"us-east-1",\
            "s3_access_key_id":"obfuscated===",\
            "s3_secret_access_key":"obfuscated===",\
            "filesystem_path":".",\
            "keep_blocked_users":"False",\
            "reset_pwd":"False",\
            "force_rand_pwd":"True",\
            "no_of_threads":"4",\
            "strip_namespace_prefix":"False",\
            "export_import_wait_time":"30"\
        }'

        with mock.patch('congregate.cli.config_test.write_to_file', mock_file):
            config_test.update_config(data)

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_parent_group_path_no_mirror_name_aws_skeleton.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)


    def test_update_config_no_changes(self):
        data = '{\
            "dstn_hostname":"hostname",\
            "dstn_access_token":"obfuscated===",\
            "import_user_id":"1",\
            "shared_runners_enabled":"True",\
            "project_suffix":"False",\
            "notification_level":"disabled",\
            "max_import_retries":"3",\
            "dstn_registry_url":"destination_registry_url",\
            "parent_group_id":"0",\
            "parent_group_path":"destination_group_full_path",\
            "privatize_groups":"True",\
            "group_sso_provider":"group_sso_provider",\
            "username_suffix":"username_suffix",\
            "mirror_username":"",\
            "src_hostname":"source_hostname",\
            "src_access_token":"obfuscated===",\
            "src_registry_url":"source_registry_url",\
            "max_export_wait_time":"3600",\
            "location":"aws",\
            "s3_name":"s3_name",\
            "s3_region":"us-east-1",\
            "s3_access_key_id":"obfuscated===",\
            "s3_secret_access_key":"obfuscated===",\
            "filesystem_path":".",\
            "keep_blocked_users":"False",\
            "reset_pwd":"True",\
            "force_rand_pwd":"False",\
            "no_of_threads":"2",\
            "strip_namespace_prefix":"True",\
            "export_import_wait_time":"30"\
        }'

        with mock.patch('congregate.cli.config_test.write_to_file', mock_file):
            update = config_test.update_config(data)

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_parent_group_path_no_mirror_name_aws_skeleton.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)
        self.assertEqual(update, "No pending config changes")


def mock_file(config):
    with open("{0}congregate.conf".format(test_dir_prefix), "w") as f:
        config.write(f)


if __name__ == "__main__":
    unittest.main()
