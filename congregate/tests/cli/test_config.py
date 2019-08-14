import unittest
import os
import mock
import responses
from congregate.cli import config
from congregate.helpers.misc_utils import get_congregate_path, input_generator
from congregate.tests.mockapi.users import MockUsersApi
from congregate.tests.mockapi.groups import MockGroupsApi
from congregate.migration.gitlab.api.users import UsersApi

class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.users_api = MockUsersApi()
        self.groups_api = MockGroupsApi()
        self.maxDiff = None

    @mock.patch.object(UsersApi, "get_current_user")
    def test_default_configuration(self, mock_get):
        values = [
            "",  # Migration source
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            os.getenv("source_instance_host"),
            os.getenv("source_instance_token"),
            os.getenv("source_instance_registry"),
            os.getenv("destination_instance_registry"),
            "",  # Parent group id
            "",  # Mirroring yes/no
            "",  # Staging location (default filesystem)
            ""  # Staging location path
        ]
        g = input_generator(values)

        expected = {
            "config": {
                "external_source": False,
                "source_instance_host": os.getenv("source_instance_host"),
                "source_instance_token": os.getenv("source_instance_token"),
                "source_instance_registry": os.getenv("source_instance_registry"),
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "destination_instance_registry": os.getenv("destination_instance_registry"),
                "number_of_threads": 2,
                "location": "filesystem",
                "import_user_id": 1,
                "path": os.getcwd()
            }
        }
        mock_get.return_value = self.users_api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch.object(UsersApi, "get_current_user")
    def test_default_configuration_with_mirror(self, mock_get):
        values = [
            "",  # Migration source
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            os.getenv("source_instance_host"),
            os.getenv("source_instance_token"),
            os.getenv("source_instance_registry"),
            os.getenv("destination_instance_registry"),
            "",  # Parent group id
            "yes",  # Mirroring yes/no
            "",  # Staging location (default filesystem)
            ""  # Staging location path
        ]
        g = input_generator(values)

        expected = {
            "config": {
                "external_source": False,
                "source_instance_host": os.getenv("source_instance_host"),
                "source_instance_token": os.getenv("source_instance_token"),
                "source_instance_registry": os.getenv("source_instance_registry"),
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "destination_instance_registry": os.getenv("destination_instance_registry"),
                "mirror_username": "root",
                "number_of_threads": 2,
                "location": "filesystem",
                "import_user_id": 1,
                "path": os.getcwd()
            }
        }
        mock_get.return_value = self.users_api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    @mock.patch.object(UsersApi, "get_current_user")
    def test_default_configuration_with_parent_id(self, mock_get, url):
        values = [
            "",  # Migration source
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            os.getenv("source_instance_host"),
            os.getenv("source_instance_token"),
            os.getenv("source_instance_registry"),
            os.getenv("destination_instance_registry"),
            "yes",  # Parent group id yes/no
            "5",  # Parent group id
            "",  # SSO yes/no
            "",  # Empty username suffix
            "",  # Mirror yes/no
            "",  # Staging location (default filesystem)
            ""   # Staging location path
        ]
        g = input_generator(values)

        expected = {
            "config": {
                "external_source": False,
                "source_instance_host": os.getenv("source_instance_host"),
                "source_instance_token": os.getenv("source_instance_token"),
                "source_instance_registry": os.getenv("source_instance_registry"),
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "destination_instance_registry": os.getenv("destination_instance_registry"),
                "number_of_threads": 2,
                "parent_id": 5,
                "parent_group_path": "twitter",
                "location": "filesystem",
                "make_visibility_private": True,
                "import_user_id": 1,
                "path": os.getcwd()
            }
        }
        url_value = "https://gitlab.com/api/v4/groups/5"
        url.return_value = url_value
        mock_get.return_value = self.users_api.get_current_user()
        responses.add(responses.GET, url_value,
                    json=self.groups_api.get_group(), status=200, content_type='text/json', match_querystring=True)

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    @mock.patch.object(UsersApi, "get_current_user")
    def test_default_configuration_with_parent_id_and_sso(self, mock_get, url):
        values = [
            "",  # Migration source
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            os.getenv("source_instance_host"),
            os.getenv("source_instance_token"),
            os.getenv("source_instance_registry"),
            os.getenv("destination_instance_registry"),
            "yes",  # Parent group id yes/no
            "5",  # Parent group id
            "yes",  # SSO yes/no
            "auth0", # SSO provider
            "", # empty username suffix
            "",  # Mirror yes/no
            "",  # Staging location (default filesystem)
            ""   # Staging location path
        ]
        g = input_generator(values)

        expected = {
            "config": {
                "external_source": False,
                "source_instance_host": os.getenv("source_instance_host"),
                "source_instance_token": os.getenv("source_instance_token"),
                "source_instance_registry": os.getenv("source_instance_registry"),
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "destination_instance_registry": os.getenv("destination_instance_registry"),
                "number_of_threads": 2,
                "parent_id": 5,
                "parent_group_path": "twitter",
                "group_sso_provider": "auth0",
                "location": "filesystem",
                "make_visibility_private": True,
                "import_user_id": 1,
                "path": os.getcwd()
            }
        }
        url_value = "https://gitlab.com/api/v4/groups/5"
        url.return_value = url_value
        mock_get.return_value = self.users_api.get_current_user()
        responses.add(responses.GET, url_value,
                    json=self.groups_api.get_group(), status=200, content_type='text/json', match_querystring=True)

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    @mock.patch.object(UsersApi, "get_current_user")
    def test_default_configuration_with_parent_id_and_sso_and_suffix(self, mock_get, url):
        values = [
            "",  # Migration source
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            os.getenv("source_instance_host"),
            os.getenv("source_instance_token"),
            os.getenv("source_instance_registry"),
            os.getenv("destination_instance_registry"),
            "yes",  # Parent group id yes/no
            "5",  # Parent group id
            "yes",  # SSO yes/no
            "auth0", # SSO provider
            "_acme", # Username suffix
            "",  # Mirror yes/no
            "",  # Staging location (default filesystem)
            ""   # Staging location path
        ]
        g = input_generator(values)

        expected = {
            "config": {
                "external_source": False,
                "source_instance_host": os.getenv("source_instance_host"),
                "source_instance_token": os.getenv("source_instance_token"),
                "source_instance_registry": os.getenv("source_instance_registry"),
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "destination_instance_registry": os.getenv("destination_instance_registry"),
                "number_of_threads": 2,
                "parent_id": 5,
                "parent_group_path": "twitter",
                "group_sso_provider": "auth0",
                "username_suffix": "_acme",
                "location": "filesystem",
                "make_visibility_private": True,
                "import_user_id": 1,
                "path": os.getcwd()
            }
        }
        url_value = "https://gitlab.com/api/v4/groups/5"
        url.return_value = url_value
        mock_get.return_value = self.users_api.get_current_user()
        responses.add(responses.GET, url_value,
                    json=self.groups_api.get_group(), status=200, content_type='text/json', match_querystring=True)

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch.object(UsersApi, "get_current_user")
    def test_explicit_default_configuration(self, mock_get):
        values = [
            "gitlab",  # migration source
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            os.getenv("source_instance_host"),
            os.getenv("source_instance_token"),
            os.getenv("source_instance_registry"),
            os.getenv("destination_instance_registry"),
            "no",
            "no",
            "filesystem",
            os.getcwd()
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "external_source": False,
                "source_instance_host": os.getenv("source_instance_host"),
                "source_instance_token": os.getenv("source_instance_token"),
                "source_instance_registry": os.getenv("source_instance_registry"),
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "destination_instance_registry": os.getenv("destination_instance_registry"),
                "number_of_threads": 2,
                "location": "filesystem",
                "import_user_id": 1,
                "path": os.getcwd()
            }
        }

        mock_get.return_value = self.users_api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch.object(UsersApi, "get_current_user")
    def test_explicit_default_configuration_with_filepath(self, mock_get):
        values = [
            "gitlab",  # Migration source
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            os.getenv("source_instance_host"),
            os.getenv("source_instance_token"),
            os.getenv("source_instance_registry"),
            os.getenv("destination_instance_registry"),
            "no",
            "no",
            "filesystem",
            "/path/to/downloads"
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "external_source": False,
                "source_instance_host": os.getenv("source_instance_host"),
                "source_instance_token": os.getenv("source_instance_token"),
                "source_instance_registry": os.getenv("source_instance_registry"),
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "destination_instance_registry": os.getenv("destination_instance_registry"),
                "number_of_threads": 2,
                "location": "filesystem",
                "import_user_id": 1,
                "path": "/path/to/downloads"
            }
        }

        mock_get.return_value = self.users_api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch.object(UsersApi, "get_current_user")
    @mock.patch('subprocess.call')
    def test_aws_configuration(self, mock_call, mock_get):
        values = [
            "gitlab",  # Migration source
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            os.getenv("source_instance_host"),
            os.getenv("source_instance_token"),
            os.getenv("source_instance_registry"),
            os.getenv("destination_instance_registry"),
            "no",
            "no",
            "aws",
            "test-bucket",
            "",
            "AKIA-Dummy",
            "asdfqwer1234"
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "access_key": "AKIA-Dummy",
                "external_source": False,
                "source_instance_host": os.getenv("source_instance_host"),
                "source_instance_token": os.getenv("source_instance_token"),
                "source_instance_registry": os.getenv("source_instance_registry"),
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "destination_instance_registry": os.getenv("destination_instance_registry"),
                "bucket_name": "test-bucket",
                "number_of_threads": 2,
                "location": "aws",
                "import_user_id": 1,
                "s3_region": "us-east-1",
                "secret_key": "asdfqwer1234"
            }
        }

        mock_get.return_value = self.users_api.get_current_user()
        mock_call.return_value = ""

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch.object(UsersApi, "get_current_user")
    @mock.patch('subprocess.call')
    def test_aws_configuration_specific_region(self, mock_call, mock_get):
        values = [
            "gitlab",  # Migration source
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            os.getenv("source_instance_host"),
            os.getenv("source_instance_token"),
            os.getenv("source_instance_registry"),
            os.getenv("destination_instance_registry"),
            "no",
            "no",
            "aws",
            "test-bucket",
            "us-west-1",
            "AKIA-Dummy",
            "asdfqwer1234"
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "access_key": "AKIA-Dummy",
                "external_source": False,
                "source_instance_host": os.getenv("source_instance_host"),
                "source_instance_token": os.getenv("source_instance_token"),
                "source_instance_registry": os.getenv("source_instance_registry"),
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "destination_instance_registry": os.getenv("destination_instance_registry"),
                "bucket_name": "test-bucket",
                "number_of_threads": 2,
                "location": "aws",
                "import_user_id": 1,
                "s3_region": "us-west-1",
                "secret_key": "asdfqwer1234"
            }
        }

        mock_get.return_value = self.users_api.get_current_user()
        mock_call.return_value = ""

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch.object(UsersApi, "get_current_user")
    def test_external_bitbucket_configuration_no_repo_list(self, mock_get):
        values = [
            "bitbucket",  # Migration source
            "user",
            "password",
            "",
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            "no",
            "no",
            "filesystem",
            os.getcwd()
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "external_source": "bitbucket",
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "external_user_password": "password",
                "external_user_name": "user",
                "number_of_threads": 2,
                "import_user_id": 1
            }
        }

        mock_get.return_value = self.users_api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch.object(UsersApi, "get_current_user")
    def test_external_bitbucket_configuration_relative_repo_list(self, mock_get):
        values = [
            "bitbucket",  # Migration source
            "user",
            "password",
            "repo_list.json",
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            "no",
            "no",
            "filesystem",
            os.getcwd()
        ]
        congregate_path = get_congregate_path()
        g = input_generator(values)
        expected = {
            "config": {
                "external_source": "bitbucket",
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "external_user_password": "password",
                "external_user_name": "user",
                "number_of_threads": 2,
                "repo_list_path": "%s/repo_list.json" % congregate_path,
                "import_user_id": 1
            }
        }

        mock_get.return_value = self.users_api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch.object(UsersApi, "get_current_user")
    def test_external_bitbucket_configuration_absolute_repo_list(self, mock_get):
        values = [
            "bitbucket",  # Migration source
            "user",
            "password",
            "/path/to/repo/list.json",
            os.getenv("destination_instance_host"),
            os.getenv("destination_instance_token"),
            "no",
            "no",
            "filesystem",
            os.getcwd()
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "external_source": "bitbucket",
                "destination_instance_host": os.getenv("destination_instance_host"),
                "destination_instance_token": os.getenv("destination_instance_token"),
                "external_user_password": "password",
                "external_user_name": "user",
                "number_of_threads": 2,
                "repo_list_path": "/path/to/repo/list.json",
                "import_user_id": 1
            }
        }

        mock_get.return_value = self.users_api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
