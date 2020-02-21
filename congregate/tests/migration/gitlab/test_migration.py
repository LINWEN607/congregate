import os
import json
import pprint
import unittest
import pytest
from congregate.cli import do_all
from congregate.migration.gitlab.diff.userdiff import UserDiffClient
from congregate.migration.gitlab.diff.groupdiff import GroupDiffClient
from congregate.migration.gitlab.diff.projectdiff import ProjectDiffClient
from congregate.helpers.base_module import app_path


@pytest.mark.e2e
class MigrationEndToEndTest(unittest.TestCase):
    def setUp(self):
        # pass
        do_all.do_all(dry_run=False)

    def test_user_migration_diff(self):
        user_diff = UserDiffClient("%s/data/user_migration_results.json" % app_path)
        print "**User Diff Results**"
        print json.dumps(user_diff.generate_report(), indent=4)

    def test_group_migration_diff(self):
        group_diff = GroupDiffClient("%s/data/group_migration_results.json" % app_path)
        print "**Group Diff Results**"
        print json.dumps(group_diff.generate_group_diff_report(), indent=4)

    def test_project_migration_diff(self):
        project_diff = ProjectDiffClient("%s/data/project_results.json" % app_path)
        print "**Project Diff Results**"
        print json.dumps(project_diff.generate_project_diff_report(), indent=4)

