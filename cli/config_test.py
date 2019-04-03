import mock
import unittest
import config
import os
from helpers.mock_api import MockApi

def input_generator(params): # generate squares as an example
    for param in params:
        yield param

class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.api = MockApi()

    @mock.patch('cli.config.get_user')
    def test_default_configuration(self, mock_get):
        values = [
            "",
            os.getenv("PARENT_INSTANCE_HOST"),
            os.getenv("PARENT_INSTANCE_TOKEN"),
            os.getenv("CHILD_INSTANCE_HOST"),
            os.getenv("CHILD_INSTANCE_TOKEN"),
            "",
            "",
            "",
            ""
        ]
        g = input_generator(values)
        expected = {
            "config": {
                "external_source": False, 
                "child_instance_token": os.getenv("CHILD_INSTANCE_TOKEN"), 
                "parent_instance_host": os.getenv("PARENT_INSTANCE_HOST"), 
                "parent_instance_token": os.getenv("PARENT_INSTANCE_TOKEN"), 
                "mirror_username": "root", 
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

if __name__ == "__main__":
    unittest.main()