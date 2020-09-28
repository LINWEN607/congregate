# TODO
    # 1. Communicate with GHE
    # 2. Import the manage_repos
    # 3. Create an ORG if it doesn't exist
    # 4. Push Repos to the org.


import mock
import os
import pytest
import unittest
from uuid import uuid4
from base64 import b64encode

from congregate.helpers.misc_utils import input_generator
from congregate.cli import config
from congregate.helpers.seed.generate_token import token_generator
from congregate.helpers.seed.generator import SeedDataGenerator
from congregate.helpers.seed.git import Manage_Repos
from congregate.migration.github.api.orgs import OrgsApi

# Create an org if it doesn't exist
# def check_org():
#     github_connection = OrgsApi(host, token)


## Placeholder

# @pytest.mark.e2e_setup
# class MigrationE2EGHETestSetup(unittest.TestCase):
#     def setUp(self):
#         # self.t = token_generator()  # this generates a GL Token, need to find out how to generate a GHE token
#         self.generate_default_config_with_tokens()
#         self.s = SeedDataGenerator()

#     def test_seed_data(self):
#         self.s.generate_seed_data(dry_run=False)

#     def generate_default_config_with_tokens(self):
#         print("Generating Destination Token")
#         destination_token = self.t.generate_token("destination_token", "2020-08-27", url=os.getenv(
#             "GITLAB_DEST"), username="root", pword=uuid4().hex)  # Destination access token
#         print("Generating Source Token")
#         source_token = self.t.generate_token("source_token", "2020-08-27", url=os.getenv(
#             "GITLAB_SRC"), username="root", pword="5iveL!fe")  # source token
#         print("Prepping config data")
#         values = [
#             os.getenv("GITLAB_DEST"),  # Destination hostname
#             # self.t.generate_token("destination_token", "2020-08-27", url=os.getenv("GITLAB_DEST"), username="root", pword=uuid4().hex), # Destination access token
#             # "0",  # Destination import user id
#             "yes",  # shared runners enabled
#             "no",  # append project suffix (retry)
#             "3",  # max_import_retries,
#             "no",  # destination parent group
#             "",  # username suffix
#             "no",  # mirror
#             "no",  # external_src_url
#             os.getenv("GITLAB_SRC"),  # source host
#             "no",  # single group migration
#             "300",  # max_export_wait_time
#             "yes",  # migrating registries
#             # self.t.generate_token("source_token", "2020-08-27", url=os.getenv("GITLAB_SRC"), username="root", pword=uuid4().hex), # source token
#             os.getenv("GITLAB_SRC_REG_URL"),  # source registry url
#             os.getenv("GITLAB_DEST_REG_URL"),  # destination registry url
#             "filesystem",  # export location
#             # "s3_name",  # bucket name
#             # "us-east-1",    # bucket region
#             # "access key",   # access key
#             # "secret key",   # secret key
#             "",  # file system path
#             "no",  # CI Source
#             "no",  # keep_blocked_users
#             "yes",  # password reset email
#             "no",  # randomized password
#             "5",  # import wait time
#             ""  # slack_url
#         ]
#         tokens = [
#             destination_token,
#             source_token
#         ]

#         g = input_generator(values)
#         t = input_generator(tokens)
#         with mock.patch('congregate.cli.config.test_registries', lambda x, y, z: None):
#             with mock.patch('builtins.input', lambda x: next(g)):
#                 with mock.patch('congregate.cli.config.obfuscate', lambda x: b64encode(next(t).encode("ascii")).decode("ascii")):
#                     config.generate_config()
