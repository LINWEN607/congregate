import unittest
from time import sleep
from pytest import mark

from congregate.cli import do_all
from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.diff.userdiff import UserDiffClient
from congregate.migration.gitlab.diff.groupdiff import GroupDiffClient
from congregate.migration.gitlab.diff.projectdiff import ProjectDiffClient
from congregate.migration.migrate import MigrateClient
from congregate.helpers.base_class import BaseClass


@mark.e2e
class MigrationEndToEndTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.b = BaseClass()
        self.migrate = MigrateClient(dry_run=False, hard_delete=True)
        do_all.list_all()
        do_all.do_all_users(dry_run=False)
        do_all.do_all_groups_and_projects(dry_run=False)

    @classmethod
    def tearDownClass(self):
        self.migrate.rollback()
        # Allow users/groups/projects to fully delete
        sleep(self.b.config.export_import_status_check_time * 6)
        rollback_diff()

    def test_user_migration_diff(self):
        user_diff = UserDiffClient(staged=True)
        diff_report = user_diff.generate_diff_report()
        user_diff.generate_html_report(
            "User", diff_report, "/data/results/user_migration_results.html")
        self.assertGreaterEqual(
            diff_report["user_migration_results"]["overall_accuracy"], 0.99)

    def test_group_migration_diff(self):
        group_diff = GroupDiffClient(staged=True)
        diff_report = group_diff.generate_diff_report()
        group_diff.generate_html_report(
            "Group", diff_report, "/data/results/group_migration_results.html")
        self.assertGreaterEqual(
            diff_report["group_migration_results"]["overall_accuracy"], 0.99)

    def test_project_migration_diff(self):
        project_diff = ProjectDiffClient(staged=True)
        diff_report = project_diff.generate_diff_report()
        project_diff.generate_html_report(
            "Project", diff_report, "/data/results/project_migration_results.html")
        self.assertGreaterEqual(
            diff_report["project_migration_results"]["overall_accuracy"], 0.99)


def rollback_diff():
    diff_report = {}
    base_diff = BaseDiffClient()
    project_diff = ProjectDiffClient(staged=True, rollback=True)
    diff_report["project_diff"] = project_diff.generate_diff_report()
    group_diff = GroupDiffClient(staged=True, rollback=True)
    diff_report["group_diff"] = group_diff.generate_diff_report()
    user_diff = UserDiffClient(staged=True, rollback=True)
    diff_report["user_diff"] = user_diff.generate_diff_report()
    base_diff.generate_html_report(
        "Rollback", diff_report, "/data/results/migration_rollback_results.html")
