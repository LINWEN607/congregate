import os
import json
import pprint
import unittest
import pytest
from congregate.cli import do_all
from congregate.migration.gitlab.diff.userdiff import UserDiffClient
from congregate.migration.gitlab.diff.groupdiff import GroupDiffClient
from congregate.helpers.base_module import app_path


@pytest.mark.e2e
class MigrationEndToEndTest(unittest.TestCase):
    def setUp(self):
        # pass
        do_all.do_all(dry_run=False)

    def test_user_migration_diff(self):
        user_diff = UserDiffClient("%s/data/user_migration_results.json" % app_path)
        print "**User Diff Results**"
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(user_diff.generate_report())

    def test_group_migration_diff(self):
        group_diff = GroupDiffClient("%s/data/group_migration_results.json" % app_path)
        print "**Group Diff Results**"
        print json.dumps(group_diff.generate_base_diff(), indent=4)






