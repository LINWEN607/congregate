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
from congregate.migration.migrate import rollback


@pytest.mark.e2e
class MigrationEndToEndTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # pass
        do_all.do_all(dry_run=False)
    
    @classmethod
    def tearDownClass(self):
        rollback(dry_run=False, hard_delete=True)

    def test_user_migration_diff(self):
        user_diff = UserDiffClient("%s/data/user_migration_results.json" % app_path)
        diff_report = user_diff.generate_report()
        self.assertGreater(diff_report["user_migration_results"]["accuracy"], 0.95)

    def test_group_migration_diff(self):
        group_diff = GroupDiffClient("%s/data/group_migration_results.json" % app_path)
        diff_report = group_diff.generate_group_diff_report()
        self.assertGreater(diff_report["group_migration_results"]["overall_accuracy"], 0.90)

    def test_project_migration_diff(self):
        project_diff = ProjectDiffClient("%s/data/project_migration_results.json" % app_path)
        diff_report = project_diff.generate_project_diff_report()
        self.assertGreater(diff_report["project_migration_results"]["overall_accuracy"], 0.90)
    

