import mock
import unittest
import config
import os

def input_generator(params): # generate squares as an example
    for param in params:
        yield param

class ConfigTests(unittest.TestCase):
    def test_default_configuration(self):
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
        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            actual = config.generate_config()
            assert expected == actual

if __name__ == "__main__":
    unittest.main()