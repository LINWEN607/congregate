import mock
import unittest
import config
import os
from congregate.helpers.mock_api import MockApi

def input_generator(params): # generate squares as an example
    for param in params:
        yield param

class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.api = MockApi()

    @mock.patch('cli.config.get_user')
    def test_default_configuration(self, mock_get):
        values = [
            "", # Migration source
            os.getenv("PARENT_INSTANCE_HOST"),
            os.getenv("PARENT_INSTANCE_TOKEN"),
            os.getenv("CHILD_INSTANCE_HOST"),
            os.getenv("CHILD_INSTANCE_TOKEN"),
            "", # Parent id
            "", # Mirroring yes/no
            "", # Staging location (default filesystem)
            ""  # Staging location path
        ]
        g = input_generator(values)

        expected = {
            "config": {
                "external_source": False, 
                "child_instance_token": os.getenv("CHILD_INSTANCE_TOKEN"), 
                "parent_instance_host": os.getenv("PARENT_INSTANCE_HOST"), 
                "parent_instance_token": os.getenv("PARENT_INSTANCE_TOKEN"), 
                "number_of_threads": 2,
                "location": "filesystem", 
                "child_instance_host": os.getenv("CHILD_INSTANCE_HOST"), 
                "parent_user_id": 1, 
                "path": os.getcwd()
            }
        }
        mock_get.return_value = self.api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)
    
    @mock.patch('cli.config.get_user')
    def test_default_configuration_with_mirror(self, mock_get):
        values = [
            "", # migration source
            os.getenv("PARENT_INSTANCE_HOST"),
            os.getenv("PARENT_INSTANCE_TOKEN"),
            os.getenv("CHILD_INSTANCE_HOST"),
            os.getenv("CHILD_INSTANCE_TOKEN"),
            "", # Parent id
            "yes", # Mirroring yes/no
            "", # Staging location (default filesystem)
            ""  # Staging location path
        ]
        g = input_generator(values)

        expected = {
            "config": {
                "external_source": False, 
                "child_instance_token": os.getenv("CHILD_INSTANCE_TOKEN"), 
                "parent_instance_host": os.getenv("PARENT_INSTANCE_HOST"), 
                "parent_instance_token": os.getenv("PARENT_INSTANCE_TOKEN"), 
                "mirror_username": "root",
                "number_of_threads": 2,
                "location": "filesystem", 
                "child_instance_host": os.getenv("CHILD_INSTANCE_HOST"), 
                "parent_user_id": 1, 
                "path": os.getcwd()
            }
        }
        mock_get.return_value = self.api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch('cli.config.get_user')
    def test_default_configuration_with_parent_id(self, mock_get):
        values = [
            "", # migration source
            os.getenv("PARENT_INSTANCE_HOST"),
            os.getenv("PARENT_INSTANCE_TOKEN"),
            os.getenv("CHILD_INSTANCE_HOST"),
            os.getenv("CHILD_INSTANCE_TOKEN"),
            "yes", # Parent id yes/no
            "5", # Parent id
            "",  # Mirror yes/no
            "",  # Staging location (default filesystem)
            ""   # Staging location path
        ]
        g = input_generator(values)

        expected = {
            "config": {
                "external_source": False, 
                "child_instance_token": os.getenv("CHILD_INSTANCE_TOKEN"), 
                "parent_instance_host": os.getenv("PARENT_INSTANCE_HOST"), 
                "parent_instance_token": os.getenv("PARENT_INSTANCE_TOKEN"), 
                "number_of_threads": 2,
                "parent_id": 5,
                "location": "filesystem", 
                "child_instance_host": os.getenv("CHILD_INSTANCE_HOST"), 
                "parent_user_id": 1, 
                "path": os.getcwd()
            }
        }
        mock_get.return_value = self.api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)
        
    @mock.patch('cli.config.get_user')
    def test_explicit_default_configuration(self, mock_get):
        values = [
            "gitlab", # migration source
            os.getenv("PARENT_INSTANCE_HOST"),
            os.getenv("PARENT_INSTANCE_TOKEN"),
            os.getenv("CHILD_INSTANCE_HOST"),
            os.getenv("CHILD_INSTANCE_TOKEN"),
            "no",
            "no",
            "filesystem",
            os.getcwd()
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "external_source": False, 
                "child_instance_token": os.getenv("CHILD_INSTANCE_TOKEN"), 
                "parent_instance_host": os.getenv("PARENT_INSTANCE_HOST"), 
                "parent_instance_token": os.getenv("PARENT_INSTANCE_TOKEN"), 
                "number_of_threads": 2,
                "location": "filesystem", 
                "child_instance_host": os.getenv("CHILD_INSTANCE_HOST"), 
                "parent_user_id": 1, 
                "path": os.getcwd()
            }
        }
        
        mock_get.return_value = self.api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch('cli.config.get_user')
    def test_explicit_default_configuration_with_filepath(self, mock_get):
        values = [
            "gitlab", # migration source
            os.getenv("PARENT_INSTANCE_HOST"),
            os.getenv("PARENT_INSTANCE_TOKEN"),
            os.getenv("CHILD_INSTANCE_HOST"),
            os.getenv("CHILD_INSTANCE_TOKEN"),
            "no",
            "no",
            "filesystem",
            "/path/to/downloads"
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "external_source": False, 
                "child_instance_token": os.getenv("CHILD_INSTANCE_TOKEN"), 
                "parent_instance_host": os.getenv("PARENT_INSTANCE_HOST"), 
                "parent_instance_token": os.getenv("PARENT_INSTANCE_TOKEN"), 
                "number_of_threads": 2,
                "location": "filesystem", 
                "child_instance_host": os.getenv("CHILD_INSTANCE_HOST"), 
                "parent_user_id": 1, 
                "path": "/path/to/downloads"
            }
        }
        
        mock_get.return_value = self.api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch('cli.config.get_user')
    @mock.patch('subprocess.call')
    def test_aws_configuration(self, mock_call, mock_get):
        values = [
            "gitlab", # migration source
            os.getenv("PARENT_INSTANCE_HOST"),
            os.getenv("PARENT_INSTANCE_TOKEN"),
            os.getenv("CHILD_INSTANCE_HOST"),
            os.getenv("CHILD_INSTANCE_TOKEN"),
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
                "child_instance_token": os.getenv("CHILD_INSTANCE_TOKEN"), 
                "parent_instance_host": os.getenv("PARENT_INSTANCE_HOST"), 
                "parent_instance_token": os.getenv("PARENT_INSTANCE_TOKEN"), 
                "bucket_name": "test-bucket",
                "number_of_threads": 2,
                "location": "aws", 
                "child_instance_host": os.getenv("CHILD_INSTANCE_HOST"), 
                "parent_user_id": 1, 
                "s3_region": "us-east-1",
                "secret_key": "asdfqwer1234"
            }
        }
        
        mock_get.return_value = self.api.get_current_user()
        mock_call.return_value = ""

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch('cli.config.get_user')
    @mock.patch('subprocess.call')
    def test_aws_configuration_specific_region(self, mock_call, mock_get):
        values = [
            "gitlab", # migration source
            os.getenv("PARENT_INSTANCE_HOST"),
            os.getenv("PARENT_INSTANCE_TOKEN"),
            os.getenv("CHILD_INSTANCE_HOST"),
            os.getenv("CHILD_INSTANCE_TOKEN"),
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
                "child_instance_token": os.getenv("CHILD_INSTANCE_TOKEN"), 
                "parent_instance_host": os.getenv("PARENT_INSTANCE_HOST"), 
                "parent_instance_token": os.getenv("PARENT_INSTANCE_TOKEN"), 
                "bucket_name": "test-bucket",
                "number_of_threads": 2,
                "location": "aws", 
                "child_instance_host": os.getenv("CHILD_INSTANCE_HOST"), 
                "parent_user_id": 1, 
                "s3_region": "us-west-1",
                "secret_key": "asdfqwer1234"
            }
        }
        
        mock_get.return_value = self.api.get_current_user()
        mock_call.return_value = ""

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch('cli.config.get_user')
    def test_external_bitbucket_configuration_no_repo_list(self, mock_get):
        values = [
            "bitbucket", # migration source
            "user",
            "password",
            "",
            os.getenv("PARENT_INSTANCE_HOST"),
            os.getenv("PARENT_INSTANCE_TOKEN"),
            os.getenv("CHILD_INSTANCE_HOST"),
            os.getenv("CHILD_INSTANCE_TOKEN"),
            "no",
            "no",
            "filesystem",
            os.getcwd()
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "external_source": "bitbucket", 
                "parent_instance_host": os.getenv("PARENT_INSTANCE_HOST"), 
                "external_user_password": "password", 
                "external_user_name": "user", 
                "number_of_threads": 2,
                "parent_instance_token": os.getenv("PARENT_INSTANCE_TOKEN"), 
                "parent_user_id": 1
            }
        }
        
        mock_get.return_value = self.api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch('cli.config.get_user')
    def test_external_bitbucket_configuration_relative_repo_list(self, mock_get):
        values = [
            "bitbucket", # migration source
            "user",
            "password",
            "repo_list.json",
            os.getenv("PARENT_INSTANCE_HOST"),
            os.getenv("PARENT_INSTANCE_TOKEN"),
            os.getenv("CHILD_INSTANCE_HOST"),
            os.getenv("CHILD_INSTANCE_TOKEN"),
            "no",
            "no",
            "filesystem",
            os.getcwd()
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "external_source": "bitbucket", 
                "parent_instance_host": os.getenv("PARENT_INSTANCE_HOST"), 
                "external_user_password": "password", 
                "external_user_name": "user", 
                "number_of_threads": 2,
                "repo_list_path": "%s/repo_list.json" % os.getenv("CONGREGATE_PATH"), 
                "parent_instance_token": os.getenv("PARENT_INSTANCE_TOKEN"), 
                "parent_user_id": 1
            }
        }
        
        mock_get.return_value = self.api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    @mock.patch('cli.config.get_user')
    def test_external_bitbucket_configuration_absolute_repo_list(self, mock_get):
        values = [
            "bitbucket", # migration source
            "user",
            "password",
            "/path/to/repo/list.json",
            os.getenv("PARENT_INSTANCE_HOST"),
            os.getenv("PARENT_INSTANCE_TOKEN"),
            os.getenv("CHILD_INSTANCE_HOST"),
            os.getenv("CHILD_INSTANCE_TOKEN"),
            "no",
            "no",
            "filesystem",
            os.getcwd()
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "external_source": "bitbucket", 
                "parent_instance_host": os.getenv("PARENT_INSTANCE_HOST"), 
                "external_user_password": "password", 
                "external_user_name": "user", 
                "number_of_threads": 2,
                "repo_list_path": "/path/to/repo/list.json", 
                "parent_instance_token": os.getenv("PARENT_INSTANCE_TOKEN"), 
                "parent_user_id": 1
            }
        }
        
        mock_get.return_value = self.api.get_current_user()

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            self.assertEqual(expected, actual)

    

if __name__ == "__main__":
    unittest.main()