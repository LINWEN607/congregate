import unittest
from time import sleep
import pytest

from congregate.cli import do_all
from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.diff.userdiff import UserDiffClient
from congregate.migration.gitlab.diff.groupdiff import GroupDiffClient
from congregate.migration.gitlab.diff.projectdiff import ProjectDiffClient
from congregate.helpers.base_class import BaseClass
from congregate.migration.migrate import rollback


@pytest.mark.e2e
class MigrationEndToEndTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.b = BaseClass()
        do_all.do_all(dry_run=False)

    @classmethod
    def tearDownClass(self):
        rollback(dry_run=False, hard_delete=True)
        # Allow users/groups/projects to fully delete
        sleep(self.b.config.importexport_wait * 5)
        rollback_diff()

    def test_user_migration_diff(self):
        user_diff = UserDiffClient(
            "/data/user_migration_results.json", staged=True)
        diff_report = user_diff.generate_diff_report()
        user_diff.generate_html_report(
            diff_report, "/data/user_migration_results.html")
        self.assertGreaterEqual(
            diff_report["user_migration_results"]["overall_accuracy"], 0.90)

    def test_group_migration_diff(self):
        group_diff = GroupDiffClient(
            "/data/group_migration_results.json", staged=True)
        diff_report = group_diff.generate_diff_report()
        group_diff.generate_html_report(
            diff_report, "/data/group_migration_results.html")
        self.assertGreaterEqual(
            diff_report["group_migration_results"]["overall_accuracy"], 0.90)

    def test_project_migration_diff(self):
        project_diff = ProjectDiffClient(
            "/data/project_migration_results.json", staged=True)
        diff_report = project_diff.generate_diff_report()
        project_diff.generate_html_report(
            diff_report, "/data/project_migration_results.html")
        self.assertGreaterEqual(
            diff_report["project_migration_results"]["overall_accuracy"], 0.90)


def rollback_diff():
    diff_report = {}
    base_diff = BaseDiffClient()
    project_diff = ProjectDiffClient(
        "/data/project_migration_results.json", staged=True, rollback=True)
    diff_report["project_diff"] = project_diff.generate_diff_report()
    group_diff = GroupDiffClient(
        "/data/group_migration_results.json", staged=True, rollback=True)
    diff_report["group_diff"] = group_diff.generate_diff_report()
    user_diff = UserDiffClient(
        "/data/user_migration_results.json", staged=True, rollback=True)
    diff_report["user_diff"] = user_diff.generate_diff_report()
    base_diff.generate_html_report(
        diff_report, "/data/migration_rollback_results.html")
