import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from pytest import mark
from congregate.cli import config
from congregate.helpers.misc_utils import input_generator
from congregate.tests.mockapi.gitlab.users import MockUsersApi
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.instance import InstanceApi

test_dir_prefix = "./congregate/tests/cli/data/"


@mark.unit_test
class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.users_api = MockUsersApi()
        self.groups_api = MockGroupsApi()
        self.maxDiff = None

    @patch.object(UsersApi, "get_current_user")
    def test_full_ext_src_skeleton_bitbucket_server(self, mock_get):
        """
            Generates a full skeleton outline of the configuration using empty strings and default values
            Compares that against the last known-good skeleton
        """
        values = [
            "hostname",  # Destination hostname
            # "token", # Destination access token
            # "0",  # Destination import user id
            "yes",   # shared runners enabled
            "no",  # append project suffix (retry)
            "3",  # max_import_retries,
            "no",  # destination parent group
            "username_suffix",  # username suffix
            "No",   # mirror
            # "mirror_username",  # mirror username
            "yes",  # external source
            "bitbucket server",  # source
            "username",  # ext_src_user
            "some_external_source",  # external_src_url
            # "password",  # ext_src_pwd
            # "token",  # ext_src_token
            "no",   # CI Source
            "no",    # keep_inactive_users
            "yes",  # password reset email
            "no",    # randomized password
            "30",   # import wait time
            "no",   # Wave spreadsheet
            "no",   # slack
            "no"    # mongo
        ]

        g = input_generator(values)

        mock_user = MagicMock()
        type(mock_user).status_code = PropertyMock(return_value=200)
        mock_user.json.return_value = self.users_api.get_current_user()
        mock_get.return_value = mock_user
        with patch('congregate.cli.config.write_to_file', mock_file):
            with patch('congregate.cli.config.app_path', "."):
                with patch('congregate.cli.config.obfuscate', lambda x: "dGVzdA=="):
                    with patch('congregate.cli.config.deobfuscate', lambda x: "dGVzdA=="):
                        with patch('getpass.getpass', lambda x: "password"):
                            with patch('builtins.input', lambda x: next(g)):
                                config.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_full_ext_src_skeleton_bitbucket_server.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)

    @patch.object(UsersApi, "get_current_user")
    def test_full_ext_src_skeleton_github_server(self, mock_get):
        """
            Generates a full skeleton outline of the configuration using empty strings and default values
            Compares that against the last known-good skeleton
        """
        values = [
            "hostname",  # Destination hostname
            # "token", # Destination access token
            # "0",  # Destination import user id
            "yes",   # shared runners enabled
            "no",  # append project suffix (retry)
            "3",  # max_import_retries,
            "no",  # destination parent group
            "username_suffix",  # username suffix
            "No",   # mirror
            # "mirror_username",  # mirror username
            "yes",  # external source
            "github",  # source
            "some_external_source",  # external_src_url
            # "password",  # ext_src_pwd
            # "token",  # ext_src_token
            "yes",   # CI SOURCE
            "Jenkins",  # ci_source
            "ci_some_external_url",  # ci_ext_src_hostname
            "ci_username",  # ci_ext_src_username
            # "token",  # ci_ext_src_token
            "no",    # keep_inactive_users
            "yes",  # password reset email
            "no",    # randomized password
            "30",   # import wait time
            "no",   # Wave spreadsheet
            "no",   # slack
            "no"    # mongo
        ]

        g = input_generator(values)

        mock_user = MagicMock()
        type(mock_user).status_code = PropertyMock(return_value=200)
        mock_user.json.return_value = self.users_api.get_current_user()
        mock_get.return_value = mock_user
        with patch('congregate.cli.config.write_to_file', mock_file):
            with patch('congregate.cli.config.app_path', "."):
                with patch('congregate.cli.config.obfuscate', lambda x: "dGVzdA=="):
                    with patch('congregate.cli.config.deobfuscate', lambda x: "dGVzdA=="):
                        with patch('getpass.getpass', lambda x: "password"):
                            with patch('builtins.input', lambda x: next(g)):
                                config.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_full_ext_src_skeleton_github_server.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)

    @patch.object(GroupsApi, "get_group")
    @patch.object(UsersApi, "get_current_user")
    @patch.object(InstanceApi, "get_current_license")
    def test_not_ext_src_src_parent_group_path_mirror_name_filesystem_skeleton(self, mock_get_license, mock_get_current_user, mock_get_group):
        """
            Not external source
            source parent group
            mirror
            filesystem
        """
        values = [
            "hostname",  # Destination hostname
            # "token", # Destination access token
            # "0",  # Destination import user id
            "yes",   # shared runners enabled
            "no",  # append project suffix (retry)
            "3",  # max_import_retries,
            "no",  # destination parent group
            "username_suffix",  # username suffix
            "Yes",   # mirror
            # "mirror_username",  # mirror username
            "no",  # external_src_url
            "source_hostname",  # source host
            # "source_access_token", # source token
            "yes",  # source parent group
            "0",   # source parent group ID
            # "source_group_full_path",   # source parent group path
            "3600",  # export_import_timeout
            "yes",  # migrating registries
            "source_registry_url",    # source registry url
            "destination_registry_url",    # destination registry url
            "filesystem",  # export location
            "absolute_path",    # file system path
            "no",   # CI Source
            "no",    # keep_inactive_users
            "yes",  # password reset email
            "no",    # randomized password
            "30",   # import wait time
            "no",   # Wave spreadsheet
            "yes",   # slack
            "https://slack.url",   # slack_url
            "no"    # mongo
        ]

        g = input_generator(values)

        mock_lic = MagicMock()
        type(mock_lic).status_code = PropertyMock(return_value=200)
        mock_lic.json.return_value = {"plan": "ultimate"}
        mock_get_license.return_value = mock_lic

        mock_user = MagicMock()
        type(mock_user).status_code = PropertyMock(return_value=200)
        mock_user.json.return_value = {
            "id": 123, "username": "username"}
        mock_get_current_user.return_value = mock_user

        class GroupHack():
            def __init__(self):
                self._json = {"full_path": "source_group_full_path"}

            def json(self):
                return self._json

        mock_get_group.return_value = GroupHack()
        with patch('congregate.cli.config.write_to_file', mock_file):
            with patch('congregate.cli.config.getcwd', lambda: "."):
                with patch('congregate.cli.config.get_congregate_path', lambda: "."):
                    with patch('congregate.cli.config.obfuscate', lambda x: "dGVzdA=="):
                        with patch('congregate.cli.config.test_registries', lambda x, y, z: None):
                            with patch('congregate.cli.config.test_slack', lambda x: None):
                                with patch('congregate.cli.config.deobfuscate', lambda x: "dGVzdA=="):
                                    with patch('builtins.input', lambda x: next(g)):
                                        config.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_src_parent_group_path_mirror_name_filesystem_skeleton.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)

    @patch.object(GroupsApi, "get_group")
    @patch.object(UsersApi, "get_current_user")
    @patch.object(InstanceApi, "get_current_license")
    def test_not_ext_src_parent_group_path_no_mirror_name_aws_default(self, mock_get_license, mock_get, mock_get_group):
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
            "yes",   # shared runners enabled
            "no",  # append project suffix (retry)
            "3",  # max_import_retries,
            "yes",  # destination parent group
            "0",  # destination parent group id
            # "dstn_parent_group_path",  # destination parent group full path
            "group_sso_provider",  # SSO provider
            "1",  # SSO provider pattern
            "username_suffix",  # username suffix
            "No",   # mirror
            # "mirror_username",  # mirror username
            "no",  # external_src_url
            "source_hostname",  # source host
            # "source_access_token", # source token
            "no",  # source parent group
            "3600",  # export_import_timeout
            "yes",  # migrating registries
            # "source_access_token", # source token
            "source_registry_url",    # source registry url
            "destination_registry_url",    # destination registry url
            "aws",  # export location
            "s3_name",  # bucket name
            "us-east-1",    # bucket region
            # "access key",   # access key
            # "secret key",   # secret key
            "absolute_path",    # file system path
            "no",   # CI Source
            "no",    # keep_inactive_users
            "yes",  # password reset email
            "no",    # randomized password
            "30",   # import wait time
            "no",   # Wave spreadsheet
            "yes",   # slack
            "https://slack.url",   # slack_url
            "no"    # mongo
        ]

        g = input_generator(values)

        mock_lic = MagicMock()
        type(mock_lic).status_code = PropertyMock(return_value=200)
        mock_lic.json.return_value = {"plan": "ultimate"}
        mock_get_license.return_value = mock_lic

        mock_user = MagicMock()
        type(mock_user).status_code = PropertyMock(return_value=200)
        mock_user.json.return_value = self.users_api.get_current_user()
        mock_get.return_value = mock_user

        class GroupHack():
            def __init__(self):
                self._json = {"full_path": "destination_group_full_path"}

            def json(self):
                return self._json

        mock_get_group.return_value = GroupHack()
        with patch('congregate.cli.config.write_to_file', mock_file):
            with patch('congregate.cli.config.getcwd', lambda: "."):
                with patch('congregate.cli.config.get_congregate_path', lambda: "."):
                    with patch('congregate.cli.config.aws.set_access_key_id', lambda x: "access_key_id"):
                        with patch('congregate.cli.config.aws.set_secret_access_key', lambda x: "secret_access_key"):
                            with patch('congregate.cli.config.obfuscate', lambda x: "dGVzdA=="):
                                with patch('congregate.cli.config.test_registries', lambda x, y, z: None):
                                    with patch('congregate.cli.config.test_slack', lambda x: None):
                                        with patch('congregate.cli.config.deobfuscate', lambda x: "dGVzdA=="):
                                            with patch('builtins.input', lambda x: next(g)):
                                                config.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_parent_group_path_no_mirror_name_aws_default.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)

    @patch.object(GroupsApi, "get_group")
    @patch.object(UsersApi, "get_current_user")
    @patch.object(InstanceApi, "get_current_license")
    def test_not_ext_src_parent_group_path_no_mirror_name_aws_default_hash_map_sso(self, mock_get_license, mock_get, mock_get_group):
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
            "yes",   # shared runners enabled
            "no",  # append project suffix (retry)
            "3",  # max_import_retries,
            "yes",  # destination parent group
            "0",  # destination parent group id
            # "dstn_parent_group_path",  # destination parent group full path
            "group_sso_provider",  # SSO provider
            "2",  # SSO provider pattern
            "path/to/file",
            "username_suffix",  # username suffix
            "No",   # mirror
            # "mirror_username",  # mirror username
            "no",  # external_src_url
            "source_hostname",  # source host
            # "source_access_token", # source token
            "no",  # source parent group
            "3600",  # export_import_timeout
            "yes",  # migrating registries
            # "source_access_token", # source token
            "source_registry_url",    # source registry url
            "destination_registry_url",    # destination registry url
            "aws",  # export location
            "s3_name",  # bucket name
            "us-east-1",    # bucket region
            # "access key",   # access key
            # "secret key",   # secret key
            "absolute_path",    # file system path
            "no",   # CI Source
            "no",    # keep_inactive_users
            "yes",  # password reset email
            "no",    # randomized password
            "30",   # import wait time
            "no",   # Wave spreadsheet
            "yes",   # slack
            "https://slack.url",   # slack_url
            "no"    # mongo
        ]

        g = input_generator(values)

        mock_lic = MagicMock()
        type(mock_lic).status_code = PropertyMock(return_value=200)
        mock_lic.json.return_value = {"plan": "ultimate"}
        mock_get_license.return_value = mock_lic

        mock_user = MagicMock()
        type(mock_user).status_code = PropertyMock(return_value=200)
        mock_user.json.return_value = self.users_api.get_current_user()
        mock_get.return_value = mock_user

        class GroupHack():
            def __init__(self):
                self._json = {"full_path": "destination_group_full_path"}

            def json(self):
                return self._json

        mock_get_group.return_value = GroupHack()
        with patch('congregate.cli.config.write_to_file', mock_file):
            with patch('congregate.cli.config.getcwd', lambda: "."):
                with patch('congregate.cli.config.get_congregate_path', lambda: "."):
                    with patch('congregate.cli.config.aws.set_access_key_id', lambda x: "access_key_id"):
                        with patch('congregate.cli.config.aws.set_secret_access_key', lambda x: "secret_access_key"):
                            with patch('congregate.cli.config.obfuscate', lambda x: "dGVzdA=="):
                                with patch('congregate.cli.config.test_registries', lambda x, y, z: None):
                                    with patch('congregate.cli.config.test_slack', lambda x: None):
                                        with patch('congregate.cli.config.deobfuscate', lambda x: "dGVzdA=="):
                                            with patch('builtins.input', lambda x: next(g)):
                                                config.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_parent_group_path_no_mirror_name_aws_hashed_sso.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)

    @patch.object(GroupsApi, "get_group")
    @patch.object(UsersApi, "get_current_user")
    @patch.object(InstanceApi, "get_current_license")
    def test_not_ext_src_parent_group_path_no_mirror_name_aws(self, mock_get_license, mock_get, mock_get_group):
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
            "no",   # shared runners enabled
            "yes",  # append project suffix (retry)
            "1",  # max_import_retries,
            "yes",  # destination parent group
            "0",  # destination parent group id
            # "dstn_parent_group_path",  # destination parent group full path
            "group_sso_provider",  # SSO provider
            "1",  # SSO provider pattern
            "_",  # username suffix
            "yes",   # mirror
            # "mirror_username",  # mirror username
            "no",  # external_src_url
            "source_hostname",  # source host
            "no",  # source parent group
            "1200",  # export_import_timeout
            "yes",  # migrating registries
            # "source_access_token", # source token
            "source_registry_url",    # source registry url
            "destination_registry_url",    # destination registry url
            "aws",  # export location
            "s3_name",  # bucket name
            "us-east-2",    # bucket region
            # "access key",   # access key
            # "secret key",   # secret key
            "/absolute_path",    # file system path
            "no",   # CI Source
            "no",    # keep_inactive_users
            "yes",  # password reset email
            "no",    # randomized password
            "60",   # import wait time
            "no",   # Wave spreadsheet
            "no",   # slack
            "no"    # mongo
        ]

        g = input_generator(values)

        mock_lic = MagicMock()
        type(mock_lic).status_code = PropertyMock(return_value=200)
        mock_lic.json.return_value = {"plan": "ultimate"}
        mock_get_license.return_value = mock_lic

        mock_user = MagicMock()
        type(mock_user).status_code = PropertyMock(return_value=200)
        mock_user.json.return_value = {"id": None, "username": None}
        mock_get.return_value = mock_user

        class GroupHack():
            def __init__(self):
                self._json = {"full_path": "destination_group_full_path"}

            def json(self):
                return self._json

        mock_get_group.return_value = GroupHack()
        with patch('congregate.cli.config.write_to_file', mock_file):
            with patch('congregate.cli.config.get_congregate_path', lambda: "."):
                with patch('congregate.cli.config.aws.set_access_key_id', lambda x: "access_key_id"):
                    with patch('congregate.cli.config.aws.set_secret_access_key', lambda x: "secret_access_key"):
                        with patch('congregate.cli.config.obfuscate', lambda x: "dGVzdA=="):
                            with patch('congregate.cli.config.test_registries', lambda x, y, z: None):
                                with patch('congregate.cli.config.deobfuscate', lambda x: "dGVzdA=="):
                                    with patch('builtins.input', lambda x: next(g)):
                                        config.generate_config()

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_parent_group_path_no_mirror_name_aws.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)

    @patch.object(GroupsApi, "get_group")
    @patch.object(UsersApi, "get_current_user")
    @patch.object(InstanceApi, "get_current_license")
    def test_not_ext_src_no_parent_group_path_mirror_name_filesystem_skeleton(self, mock_get_license, mock_get_current_user, mock_get_group):
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
            "yes",   # shared runners enabled
            "no",  # append project suffix (retry)
            "3",  # max_import_retries,
            "no",  # destination parent group
            "username_suffix",  # username suffix
            "Yes",   # mirror
            # "mirror_username",  # mirror username
            "no",  # external_src_url
            "source_hostname",  # source host
            # "source_access_token", # source token
            "no",  # source parent group
            "3600",  # export_import_timeout
            "yes",  # migrating registries
            "source_registry_url",    # source registry url
            "destination_registry_url",    # destination registry url
            "filesystem",  # export location
            "absolute_path",    # file system path
            "no",    # CI SOURCE
            "no",    # keep_inactive_users
            "yes",  # password reset email
            "no",    # randomized password
            "30",   # import wait time
            "no",   # Wave spreadsheet
            "yes",   # slack
            "https://slack.url",   # slack_url
            "no"    # mongo
        ]

        g = input_generator(values)

        mock_lic = MagicMock()
        type(mock_lic).status_code = PropertyMock(return_value=200)
        mock_lic.json.return_value = {"plan": "ultimate"}
        mock_get_license.return_value = mock_lic

        mock_user = MagicMock()
        type(mock_user).status_code = PropertyMock(return_value=200)
        mock_user.json.return_value = {
            "id": 123, "username": "username"}
        mock_get_current_user.return_value = mock_user

        class GroupHack():
            def __init__(self):
                self._json = {"full_path": None}

            def json(self):
                return self._json

        mock_get_group.return_value = GroupHack()

        with patch('congregate.cli.config.write_to_file', mock_file):
            with patch('congregate.cli.config.getcwd', lambda: "."):
                with patch('congregate.cli.config.get_congregate_path', lambda: "."):
                    with patch('congregate.cli.config.obfuscate', lambda x: "dGVzdA=="):
                        with patch('congregate.cli.config.test_registries', lambda x, y, z: None):
                            with patch('congregate.cli.config.test_slack', lambda x: None):
                                with patch('congregate.cli.config.deobfuscate', lambda x: "dGVzdA=="):
                                    with patch('builtins.input', lambda x: next(g)):
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
            "dstn_access_token":"dGVzdA==",\
            "import_user_id":"1",\
            "shared_runners_enabled":"False",\
            "project_suffix":"False",\
            "max_import_retries":"3",\
            "username_suffix":"local",\
            "mirror_username":"",\
            "src_hostname":"source_hostname",\
            "src_access_token":"dGVzdA==",\
            "src_parent_group_id":"0",\
            "src_parent_group_path":"source_group_full_path",\
            "export_import_timeout":"3600",\
            "src_registry_url":"source_registry_url",\
            "dstn_registry_url":"destination_registry_url",\
            "location":"aws",\
            "s3_name":"s3_name",\
            "s3_region":"us-east-1",\
            "s3_access_key_id":"dGVzdA==",\
            "s3_secret_access_key":"dGVzdA==",\
            "filesystem_path":".",\
            "keep_inactive_users":"False",\
            "reset_pwd":"False",\
            "force_rand_pwd":"True",\
            "export_import_status_check_time":"30",\
            "slack_url":"https://slack.url"\
        }'

        with patch('congregate.cli.config.write_to_file', mock_file):
            config.update_config(data)

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_src_parent_group_path_mirror_name_filesystem_skeleton.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)

    def test_update_config_no_changes(self):
        data = '{\
            "dstn_hostname":"hostname",\
            "dstn_access_token":"dGVzdA==",\
            "import_user_id":"1",\
            "shared_runners_enabled":"True",\
            "project_suffix":"False",\
            "max_import_retries":"3",\
            "username_suffix":"username_suffix",\
            "mirror_username":"",\
            "src_hostname":"source_hostname",\
            "src_access_token":"dGVzdA==",\
            "src_parent_group_id":"0",\
            "src_parent_group_path":"source_group_full_path",\
            "export_import_timeout":"3600",\
            "src_registry_url":"source_registry_url",\
            "dstn_registry_url":"destination_registry_url",\
            "location":"aws",\
            "s3_name":"s3_name",\
            "s3_region":"us-east-1",\
            "s3_access_key_id":"dGVzdA==",\
            "s3_secret_access_key":"dGVzdA==",\
            "filesystem_path":".",\
            "keep_inactive_users":"False",\
            "reset_pwd":"True",\
            "force_rand_pwd":"False",\
            "export_import_status_check_time":"30",\
            "slack_url":"https://slack.url"\
        }'

        with patch('congregate.cli.config.write_to_file', mock_file):
            update = config.update_config(data)

        # load the file that was just written
        with open("{0}congregate.conf".format(test_dir_prefix), "r") as f:
            generated = f.readlines()

        # load the reference file
        with open("{0}test_not_ext_src_src_parent_group_path_mirror_name_filesystem_skeleton.conf".format(test_dir_prefix), "r") as f:
            reference = f.readlines()

        self.assertListEqual(generated, reference)
        self.assertEqual(update, "No pending config changes")


def mock_file(conf):
    with open("{0}congregate.conf".format(test_dir_prefix), "w") as f:
        conf.write(f)


if __name__ == "__main__":
    unittest.main()
