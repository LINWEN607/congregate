import os
import unittest
from uuid import uuid4
import base64
import json
import pytest
import mock
from congregate.helpers.misc_utils import input_generator
from congregate.cli import config
from congregate.helpers.seed.generate_token import token_generator
from congregate.helpers.seed.generator import SeedDataGenerator


@pytest.mark.e2e_setup
class MigrationEndToEndTestSetup(unittest.TestCase):
    def setUp(self):
        self.t = token_generator()
        self.generate_default_config_with_tokens()
        self.s = SeedDataGenerator()
        # self.s.generate_seed_data(dry_run=False)

    def test_seed_data(self):
        self.s.generate_seed_data(dry_run=False)

    def generate_default_config_with_tokens(self):
        print "Generating Destination Token"
        destination_token = self.t.generate_token("destination_token", "2020-08-27", url=os.getenv(
            "GITLAB_DEST"), username="root", pword=uuid4().hex)  # Destination access token
        print "Generating Source Token"
        source_token = self.t.generate_token("source_token", "2020-08-27", url=os.getenv(
            "GITLAB_SRC"), username="root", pword="5iveL!fe")  # source token
        print "Prepping config data"
        values = [
            os.getenv("GITLAB_DEST"),  # Destination hostname
            # self.t.generate_token("destination_token", "2020-08-27", url=os.getenv("GITLAB_DEST"), username="root", pword=uuid4().hex), # Destination access token
            # "0",  # Destination import user id
            "True",  # shared runners enabled
            "False",  # append project suffix (retry)
            "3",  # max_import_retries,
            "gitlab",  # external_src_url
            os.getenv("GITLAB_SRC"),  # source host
            # self.t.generate_token("source_token", "2020-08-27", url=os.getenv("GITLAB_SRC"), username="root", pword=uuid4().hex), # source token
            os.getenv("GITLAB_SRC_REG_URL"),  # source registry url
            "60",  # max_export_wait_time
            os.getenv("GITLAB_DEST_REG_URL"),  # destination registry url
            "",  # destination parent group id
            # "parent_group_path",  # destination parent group full path
            # "group_sso_provider",  # SSO provider
            "",  # username suffix
            "No",  # mirror
            "filesystem",  # export location
            # "s3_name",  # bucket name
            # "us-east-1",    # bucket region
            # "access key",   # access key
            # "secret key",   # secret key
            "",  # file system path
            "False",  # keep_blocked_users
            "True",  # password reset email
            "False",  # randomized password
            "10"  # import wait time
        ]
        print json.dumps(values)
        tokens = [
            destination_token,
            source_token
        ]

        g = input_generator(values)
        t = input_generator(tokens)
        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            with mock.patch('congregate.cli.config.obfuscate', lambda x: base64.b64encode(next(t))):
                config.generate_config()
