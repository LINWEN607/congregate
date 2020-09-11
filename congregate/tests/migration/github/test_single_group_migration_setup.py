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

import sys

from congregate.helpers.base_class import BaseClass
from congregate.helpers.seed.git import Manage_Repos
from congregate.migration.github.api.orgs import OrgsApi
from congregate.migration.github.api.repos import ReposApi


class Seed_GHE(BaseClass):
    '''
    Dunno what I'm doing here :D
    '''
    def __init__(self):
        self.manage_repos = Manage_Repos(size='medium', clone=True, remote_name='fitall')
        super(Seed_GHE, self).__init__()
        self.orgs_api = OrgsApi(self.config.source_host, self.config.source_token)
        self.repos_api = ReposApi(self.config.source_host, self.config.source_token)

        self.repos = self.manage_repos.repos

    def create_org(self, org, owner='mlindsay'):
        '''
        Create an ORG in GHE
        '''
        orgs = self._get_remote_orgs()
        print(orgs)

        if self._check_org_exists(org, orgs):
            print("ERROR: Wouldn't be prudent. Org already exists")
            sys.exit()
        else:
            data = {
                'login': org,
                'admin': owner
            }
            temp = self.orgs_api.create_org(data=data)

    def create_repo(self, org, repo):
        data = {
            'name': repo,
        }
        temp = self.repos_api.create_org_repo(org_name=org, data=data)

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


test = Seed_GHE()
print(len(test.repos))

# print(test.repo_map)
# test.create_org("Mike-Test")
# test.create_repo("Mike-Test", "Mike-Repo-1")
# print(type(t))
