import os
import unittest
from unittest import mock
from base64 import b64encode
from pytest import mark
from gitlab_ps_utils.misc_utils import input_generator, safe_json_response
from congregate.cli import config
from congregate.helpers.seed.generate_token import token_generator
from congregate.helpers.seed.generator import SeedDataGenerator
from congregate.migration.gitlab.api.groups import GroupsApi

@mark.e2e_gl_setup_3
class MigrationEndToEndTestSetup(unittest.TestCase):
    def setUp(self):
        self.t = token_generator()
        print("Generating Destination Token")
        self.dest_token = self.t.generate_pat_from_oauth_token(url=os.getenv(
            "GITLAB_DEST"), username="root", pword=os.getenv('GITLAB_ROOT_PASSWORD'))  # Destination access token
        print("Generating Source Token")
        self.src_token = self.t.generate_pat_from_oauth_token(url=os.getenv(
            "GITLAB_SRC"), username="root", pword=os.getenv('GITLAB_ROOT_PASSWORD'))  # Source access token
        self.generate_single_group_config_with_tokens()
        self.s = SeedDataGenerator()
        # group_path = safe_json_response(GroupsApi().get_group(3, os.getenv('GITLAB_SRC'), self.src_token)).get('full_path')
        

    def test_seed_data(self):
        _, groups, _ = self.s.generate_seed_data(dry_run=False)
        group_id = groups[-1]['id']
        self.src_token = self.t.generate_group_access_owner_token(os.getenv(
            "GITLAB_SRC"), self.src_token, group_id)
        self.generate_single_group_config_with_tokens(str(group_id))

    def generate_single_group_config_with_tokens(self, group_id="1"):
        # print("Generating Destination Token")
        # destination_token = self.t.generate_token("destination_token", url=os.getenv(
        #     "GITLAB_DEST"), username="root", pword="5iveL!fe")  # Destination access token
        # print("Generating Source Token")
        # source_token = self.t.generate_token("source_token", url=os.getenv(
        #     "GITLAB_SRC"), username="root", pword="5iveL!fe")  # source token
        print("Prepping config data")
        values = [
            os.getenv("GITLAB_DEST"),  # Destination hostname
            # destination_token
            # "0",  # Destination import user id
            "yes",  # shared runners enabled
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
            group_id,   # source parent group ID
            # "source_group_full_path",   # source parent group path
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
            "300",  # export_import_timeout
            "no",  # wave spreadsheet
            "no",  # slack_url
            "yes",  # external mongo host
            "mongo"  # mongo host
            # mongo_port
            # ui_port
            # processes
        ]
        tokens = [
            self.dest_token,
            self.src_token
        ]

        g = input_generator(values)
        t = input_generator(tokens)
        with mock.patch('congregate.cli.config.test_registries', lambda x, y, z: None):
            with mock.patch('builtins.input', lambda x: next(g)):
                with mock.patch('congregate.cli.config.obfuscate', lambda x: b64encode(next(t).encode("ascii")).decode("ascii")):
                    config.generate_config()
