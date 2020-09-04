import os
import unittest
from uuid import uuid4
from base64 import b64encode
import pytest
import mock
from congregate.helpers.misc_utils import input_generator
from congregate.cli import config
from congregate.helpers.seed.generate_token import token_generator
from congregate.helpers.seed.generator import SeedDataGenerator

from congregate.helpers.base_class import BaseClass
from congregate.helpers.seed.git import Manage_Repos
from congregate.migration.github.api.orgs import OrgsApi
from congregate.migration.github.api.repos import ReposApi


class Single_Group_Migration(BaseClass):
    '''
    Dunno what I'm doing here :D
    '''

    def __init__(self):
        super(Single_Group_Migration, self).__init__()
        self.orgs_api = OrgsApi(self.config.source_host, self.config.source_token)
        self.repos_api = ReposApi(self.config.source_host, self.config.source_token)
        self.manage_repos = Manage_Repos()

        self.repos = self._get_seed_repos()

    def create_org(self, org):
        '''
        Create an ORG in GHE
        '''
        orgs = self._get_remote_orgs()
        if self._check_org_exists(org, orgs):
            print("ERROR: Wouldn't be prudent")
        else:
            temp = self.orgs_api.create_org(data=org)
            print(temp)

    def _get_seed_repos(self):
        '''
        This should only get our list of repos.
        '''
        return self.manage_repos.repos

    def _check_org_exists(self, org, orgs):
        for record in orgs:
            if org == record['login']:
                return True

    def _get_remote_orgs(self):
        return self.orgs_api.get_all_orgs()

    def check_repos_are_local(self):  # See if we already have the repos downloaded
        pass

    def clone_repos(self):  # Clone the repos
        pass


test = Single_Group_Migration()
test.create_org("Mike-Test")

# print(test.orgs_api.create_org(self, data=None, message=None)
# for org in test.orgs_api.get_all_orgs():
#     print(org['login'])


# pull in the list of repos based off size
# reorigin the list of repos
# Create the Org on GHE? @leopardm
# Create the repos on GHE
# Push the repos to GHE


## PLACEHOLDER

# @pytest.mark.e2e_setup_2
# class MigrationEndToEndTestSetup(unittest.TestCase):
#     def setUp(self):
#         self.t = token_generator()
#         self.generate_single_group_config_with_tokens()
#         self.s = SeedDataGenerator()

#     def test_seed_data(self):
#         self.s.generate_seed_data(dry_run=False)

#     def generate_single_group_config_with_tokens(self):
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
#             "yes",  # source parent group
#             "2",   # source parent group ID
#             # "source_group_full_path",   # source parent group path
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
