import os
import unittest
from uuid import uuid4
import base64
import pytest
import mock
import json
import pprint
from congregate.helpers.misc_utils import input_generator
from congregate.cli import config, do_all
from congregate.helpers.seed.generate_token import token_generator
from congregate.helpers.seed.generator import SeedDataGenerator
from congregate.migration.gitlab.compare import CompareClient
from congregate.migration.gitlab.diff.userdiff import UserDiffClient
from congregate.helpers.base_module import app_path


@pytest.mark.e2e
class MigrationEndToEndTest(unittest.TestCase):
    def setUp(self):
        # pass
        do_all.do_all(dry_run=False)
    #     self.t = token_generator()
    #     self.generate_default_config_with_tokens()
    #     self.s = SeedDataGenerator()
    #     self.s.generate_seed_data(dry_run=False)

    # def test_seed_data(self):
    #     self.s.generate_seed_data(dry_run=False)

    def test_migration(self):
        # reinitializing config class in do_all module
        # do_all.b.config = do_all.b.ConfigurationValidator()
        # do_all.do_all(dry_run=False)
        user_diff = UserDiffClient("%s/data/user_migration_results.json" % app_path)
        print "**User Diff Results**"
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(user_diff.generate_report())






