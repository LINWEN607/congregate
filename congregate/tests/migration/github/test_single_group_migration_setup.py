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
    def __init__(self, seeds_count=60, size_ratio=.9, organization="Mike-Test", owner="mlindsay"):
        super(Seed_GHE, self).__init__()
        self.manage_repos = Manage_Repos(size='medium')
        self.orgs_api = OrgsApi(self.config.source_host, self.config.source_token)
        self.repos_api = ReposApi(self.config.source_host, self.config.source_token)
        self.seeds_count = seeds_count

        self.repos = self.manage_repos.repos
        self.repo_map = self.manage_repos.repo_map
        self.organization = organization
        self.owner = owner

    # TODO: Create a number of repos in github == to self.seeds_count
    # TODO: Reorigin the existing local repos
    # TODO: Push the repos up to GHE.

    def define_seed_repos(self):
        '''
        Using our self.seeds_count, self.size_ratio, and self.repos, create unique names for each repo to fill
        out the complete list of repos we need to work with.
        '''
        new_repos = []
        no_repos = len(self.repos)
        i = 0
        while True:
            cur = i - (i // no_repos) * no_repos
            new_repos.append(f"{self.repos[cur]}-loop-{i // no_repos}")
            i += 1
            if i == self.seeds_count - 1:
                break
        self.repos = new_repos

    def create_org(self):
        '''
        Create an ORG in GHE
        '''
        orgs = self._get_remote_orgs()

        if self._check_org_exists(org, orgs):
            print("ERROR: Wouldn't be prudent. Org already exists")
            sys.exit()
        else:
            data = {
                'login': self.organization,
                'admin': self.owner
            }
            self.orgs_api.create_org(data=data)

    def create_repo(self, repo):
        data = {
            'name': repo,
        }
        self.repos_api.create_org_repo(org_name=self.organization, data=data)

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
test.define_seed_repos()
for repo in test.repos:
    test.create_repo(repo)

print(test.repos)
# print(f"\n{test.repo_map}\n")
# print(test.__dict__)

# print(test.repo_map)
# test.create_org("Mike-Test")
# test.create_repo("Mike-Test", "Mike-Repo-1")
# print(type(t))
