import os
import unittest
from unittest import mock
from base64 import b64encode
from pytest import mark
from gitlab_ps_utils.misc_utils import input_generator
from congregate.cli import config
from congregate.helpers.seed.generate_token import token_generator
from congregate.helpers.seed.generator import SeedDataGenerator


@mark.e2e_gl_setup_2
class MigrationEndToEndTestSetup(unittest.TestCase):
    def setUp(self):
        self.t = token_generator()
        self.generate_single_group_config_with_tokens()
        self.s = SeedDataGenerator()

    def test_seed_data(self):
        self.s.generate_seed_data(dry_run=False)

    def generate_single_group_config_with_tokens(self):
        print("Generating Destination Token")
        destination_token = self.t.generate_token("destination_token", url=os.getenv(
            "GITLAB_DEST"), username="root", pword="5iveL!fe")  # Destination access token
        print("Generating Source Token")
        source_token = self.t.generate_token("source_token", url=os.getenv(
            "GITLAB_SRC"), username="root", pword="5iveL!fe")  # source token
        print("Prepping config data")
        values = [
            os.getenv("GITLAB_DEST"),  # Destination hostname
            # destination_token
            # "0",  # Destination import user id
            "yes",  # shared runners enabled
            "no",  # append project suffix (retry)
            "3",  # max_import_retries,
            "no",  # destination parent group
            "",  # username suffix
            "no",  # mirror
            # max_asset_expiration_time
            "no",  # external_src_url
            # src_type
            os.getenv("GITLAB_SRC"),  # source host
            # src_access_token
            # src_tier
            "yes",  # source parent group
            "3",   # source parent group ID
            # "source_group_full_path",   # source parent group path
            "300",  # export_import_timeout
            "yes",  # migrating registries
            # source_token
            os.getenv("GITLAB_SRC_REG_URL"),  # source registry url
            os.getenv("GITLAB_DEST_REG_URL"),  # destination registry url
            "filesystem",  # export location
            # "s3_name",  # bucket name
            # "us-east-1",    # bucket region
            # "access key",   # access key
            # "secret key",   # secret key
            "",  # filesystem_path
            "no",  # CI Source
            "no",  # keep_inactive_users
            "yes",  # reset_pwd
            "no",  # force_rand_pwd
            "5",  # export_import_status_check_time
            "no",  # wave spreadsheet
            "no",  # slack_url
            "yes",  # external mongo host
            "mongo"  # mongo host
            # mongo_port
            # ui_port
            # processes
        ]
        tokens = [
            destination_token,
            source_token
        ]

        g = input_generator(values)
        t = input_generator(tokens)
        with mock.patch('congregate.cli.config.test_registries', lambda x, y, z: None):
            with mock.patch('builtins.input', lambda x: next(g)):
                with mock.patch('congregate.cli.config.obfuscate', lambda x: b64encode(next(t).encode("ascii")).decode("ascii")):
                    config.generate_config()
