import os
import unittest
from uuid import uuid4

import pytest
import mock
from congregate.helpers.misc_utils import input_generator
from congregate.cli import config
from congregate.helpers.seed.generate_token import token_generator
from congregate.helpers.seed.generator import SeedDataGenerator


@pytest.mark.e2e
class MigrationEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.t = token_generator()
        self.generate_default_config_with_tokens()
        self.s = SeedDataGenerator()

    def test_seed_data(self):
        self.s.generate_seed_data(dry_run=False)

    def generate_default_config_with_tokens(self):
        values = [
            os.getenv("GITLAB_DEST"), # Destination hostname
            self.t.generate_token("destination_token", "2020-08-27", url=os.getenv("GITLAB_DEST"), username="root", pword=uuid4().hex), # Destination access token
            # "0",  # Destination import user id
            "True",   # shared runners enabled
            "False",  # append project suffix (retry)
            "disabled", # notification level
            "3",  # max_import_retries,
            "gitlab", # external_src_url
            os.getenv("GITLAB_SRC"), # source host
            self.t.generate_token("source_token", "2020-08-27", url=os.getenv("GITLAB_SRC"), username="root", pword=uuid4().hex), # source token
            os.getenv("registry_url"),    # source registry url
            "3600", # max_export_wait_time
            os.getenv("registry_url"),    # destination registry url
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
        # values = [
        #     "",  # Migration source
        #     os.getenv("GITLAB_DEST"),
        #     self.t.generate_token("destination_token", "2020-08-27", url=os.getenv("GITLAB_DEST"), username="root", pword=uuid4().hex),
        #     os.getenv("GITLAB_SRC"),
        #     self.t.generate_token("source_token", "2020-08-27", url=os.getenv("GITLAB_SRC"), username="root", pword=uuid4().hex),
        #     os.getenv("source_instance_registry"),
        #     os.getenv("destination_instance_registry"),
        #     "",  # Parent group id
        #     "",  # Mirroring yes/no
        #     "",  # Staging location (default filesystem)
        #     "",  # Staging location path
        #     "",     # reset_password
        #     ""      # force_random_password
        # ]

        g = input_generator(values)

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            config.config()


