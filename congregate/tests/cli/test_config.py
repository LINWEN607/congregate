import unittest
import mock
from congregate.cli import config
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
            "hostname",  # Destination hostname
            # "token", # Destination access token
            # "0",  # Destination import user id
            "True",   # shared runners enabled
            "False",  # append project suffix (retry)
            "3",  # max_import_retries,
            "some_external_source",  # external_src_url
            "username",  # ext_src_user
            "repo_path",  # ext_src_repo
            "False",    # keep_blocked_users
            "True",  # password reset email
            "False",    # randomized password
            "30"   # import wait time
        ]

        g = input_generator(values)

        mock_get.return_value = self.users_api.get_current_user()
        with mock.patch('congregate.cli.config.write_to_file', mock_file):
            with mock.patch('congregate.cli.config.app_path', "."):
                with mock.patch('congregate.cli.config.obfuscate', lambda x: "obfuscated==="):
                    with mock.patch('congregate.cli.config.deobfuscate', lambda x: "deobfuscated==="):
                        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
                            config.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_full_ext_src_skeleton.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)

    @mock.patch.object(GroupsApi, "get_group")
    @mock.patch.object(UsersApi, "get_current_user")
    def test_not_ext_src_parent_group_path_no_mirror_name_aws_default(self, mock_get, mock_get_group):
        """
            Not external source
            parent group found (first if)
            No mirror (default)
            AWS (first if)
        """
        values = [
            "hostname",  # Destination hostname
            # "token", # Destination access token
            # "0",  # Destination import user id
            "True",   # shared runners enabled
            "False",  # append project suffix (retry)
            "3",  # max_import_retries,
            "gitlab",  # external_src_url
            "source_hostname",  # source host
            # "source_access_token", # source token
            "source_registry_url",    # source registry url
            "3600",  # max_export_wait_time
            "destination_registry_url",    # destination registry url
            "0",  # destination parent group id
            # "parent_group_path",  # destination parent group full path
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
        with mock.patch('congregate.cli.config.write_to_file', mock_file):
            with mock.patch('congregate.cli.config.getcwd', lambda: "."):
                with mock.patch('congregate.cli.config.get_congregate_path', lambda: "."):
                    with mock.patch('congregate.cli.config.aws.set_access_key_id', lambda x: "access_key_id"):
                        with mock.patch('congregate.cli.config.aws.set_secret_access_key', lambda x: "secret_access_key"):
                            with mock.patch('congregate.cli.config.obfuscate', lambda x: "obfuscated==="):
                                with mock.patch('congregate.cli.config.deobfuscate', lambda x: "deobfuscated==="):
                                    with mock.patch('__builtin__.raw_input', lambda x: next(g)):
                                        config.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_parent_group_path_no_mirror_name_aws_default.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)

    @mock.patch.object(GroupsApi, "get_group")
    @mock.patch.object(UsersApi, "get_current_user")
    def test_not_ext_src_parent_group_path_no_mirror_name_aws(self, mock_get, mock_get_group):
        """
            Not external source
            No import user ID or username
            parent group found (first if)
            mirror
            AWS (first if)
            Non-default
        """
        values = [
            "hostname",  # Destination hostname
            # "token", # Destination access token
            # "0",  # Destination import user id
            "False",   # shared runners enabled
            "True",  # append project suffix (retry)
            "1",  # max_import_retries,
            "gitlab",  # external_src_url
            "source_hostname",  # source host
            # "source_access_token", # source token
            "source_registry_url",    # source registry url
            "1200",  # max_export_wait_time
            "destination_registry_url",    # destination registry url
            "0",  # destination parent group id
            # "parent_group_path",  # destination parent group full path
            "group_sso_provider",  # SSO provider
            "_",  # username suffix
            "Yes",   # mirror
            # "mirror_username",  # mirror username
            "aws",  # export location
            "s3_name",  # bucket name
            "us-east-2",    # bucket region
            # "access key",   # access key
            # "secret key",   # secret key
            "/absolute_path",    # file system path
            "True",    # keep_blocked_users
            "False",  # password reset email
            "True",    # randomized password
            "60"   # import wait time
        ]

        g = input_generator(values)

        mock_get.return_value = {"id": None, "username": None}

        class Hack(object):
            def __init__(self):
                self._json = {"full_path": "destination_group_full_path"}

            def json(self):
                return self._json

        mock_get_group.return_value = Hack()
        with mock.patch('congregate.cli.config.write_to_file', mock_file):
            with mock.patch('congregate.cli.config.get_congregate_path', lambda: "."):
                with mock.patch('congregate.cli.config.aws.set_access_key_id', lambda x: "access_key_id"):
                    with mock.patch('congregate.cli.config.aws.set_secret_access_key', lambda x: "secret_access_key"):
                        with mock.patch('congregate.cli.config.obfuscate', lambda x: "obfuscated==="):
                            with mock.patch('congregate.cli.config.deobfuscate', lambda x: "deobfuscated==="):
                                with mock.patch('__builtin__.raw_input', lambda x: next(g)):
                                    config.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_parent_group_path_no_mirror_name_aws.conf".format(test_dir_prefix), "r") as f:
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
            "hostname",  # Destination hostname
            # "token", # Destination access token
            # "0",  # Destination import user id
            "True",   # shared runners enabled
            "False",  # append project suffix (retry)
            "3",  # max_import_retries,
            "gitlab",  # external_src_url
            "source_hostname",  # source host
            # "source_access_token", # source token
            "source_registry_url",    # source registry url
            "3600",  # max_export_wait_time
            "destination_registry_url",    # destination registry url
            "0",  # destination parent group id
            # "parent_group_path",  # destination parent group full path
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
            "30"   # import wait time
        ]

        g = input_generator(values)

        mock_get_current_user.return_value = {
            "id": 123, "username": "username"}

        class GroupHack(object):
            def __init__(self):
                self._json = {"full_path": None}

            def json(self):
                return self._json

        mock_get_group.return_value = GroupHack()

        with mock.patch('congregate.cli.config.write_to_file', mock_file):
            with mock.patch('congregate.cli.config.getcwd', lambda: "."):
                with mock.patch('congregate.cli.config.get_congregate_path', lambda: "."):
                    with mock.patch('congregate.cli.config.obfuscate', lambda x: "obfuscated==="):
                        with mock.patch('congregate.cli.config.deobfuscate', lambda x: "deobfuscated==="):
                            with mock.patch('__builtin__.raw_input', lambda x: next(g)):
                                config.generate_config()

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
            "max_import_retries":"3",\
            "dstn_registry_url":"destination_registry_url",\
            "parent_group_id":"1",\
            "parent_group_path":"destination_group_full_path",\
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
            "export_import_wait_time":"30"\
        }'

        with mock.patch('congregate.cli.config.write_to_file', mock_file):
            config.update_config(data)

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_parent_group_path_no_mirror_name_aws_default.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)

    def test_update_config_no_changes(self):
        data = '{\
            "dstn_hostname":"hostname",\
            "dstn_access_token":"obfuscated===",\
            "import_user_id":"1",\
            "shared_runners_enabled":"True",\
            "project_suffix":"False",\
            "max_import_retries":"3",\
            "dstn_registry_url":"destination_registry_url",\
            "parent_group_id":"0",\
            "parent_group_path":"destination_group_full_path",\
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
            "export_import_wait_time":"30"\
        }'

        with mock.patch('congregate.cli.config.write_to_file', mock_file):
            update = config.update_config(data)

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_parent_group_path_no_mirror_name_aws_default.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)
        self.assertEqual(update, "No pending config changes")


def mock_file(conf):
    with open("{0}congregate.conf".format(test_dir_prefix), "w") as f:
        conf.write(f)


if __name__ == "__main__":
    unittest.main()
