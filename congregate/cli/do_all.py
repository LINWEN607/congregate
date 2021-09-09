import json

from congregate.cli.stage_groups import GroupStageCLI
from congregate.cli.list_source import list_data
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.migrate import MigrateClient
from congregate.helpers.base_class import BaseClass
from congregate.helpers.list_utils import remove_dupes
from congregate.helpers.file_utils import is_recent_file

users = UsersClient()
groups = GroupsClient()
b = BaseClass()

"""
    CLI utility to run a full migration without specifically staging data
"""


def do_all_users(dry_run=True):
    """
        Stages all users and migrates users to destination instance

        :param: dry_run (bool) If true, will write POST request payload to JSON files for review. If false, will conduct full user migration
    """
    # Clear staged projects and groups and stage only users
    gcli = GroupStageCLI()
    gcli.stage_data([""], dry_run=False)
    with open("{}/data/users.json".format(b.app_path), "r") as u:
        with open("{}/data/staged_users.json".format(b.app_path), "w") as su:
            json.dump(remove_dupes(json.load(u)), su, indent=4)

    migrate = MigrateClient(
        dry_run=dry_run,
        skip_group_export=True,
        skip_group_import=True,
        skip_project_import=True,
        skip_project_export=True
    )
    migrate.migrate()

    # (14.2.2+) Set public_email field for all staged users on src/dest before group/project export/import
    users.set_staged_users_public_email(dry_run=False)
    users.set_staged_users_public_email(dry_run=False, dest=True)

    # Lookup NOT found users AFTER - NO dry run
    users.search_for_staged_users()


def do_all_groups_and_projects(dry_run=True):
    """
        Stages all groups and projects and migrates them to the destination instance

        :param: dry_run (bool) If true, will write POST request payload to JSON files for review. If false, will conduct full group and project migration
    """
    # Stage ALL - NO dry run
    gcli = GroupStageCLI()
    gcli.stage_data(["all"], dry_run=False)

    migrate = MigrateClient(dry_run=dry_run, skip_users=True)
    migrate.migrate()


def do_all(dry_run=True):
    """
        Stages all users, groups, and projects and migrates them to the destination instance

        :param: dry_run (bool) If true, will write POST request payload to JSON files for review. If false, will conduct full migration
    """
    # Stage ALL - NO dry run
    gcli = GroupStageCLI()
    gcli.stage_data(["all"], dry_run=False)

    migrate = MigrateClient(dry_run=dry_run)
    migrate.migrate()


def list_all():
    """
        Checks if data has been retrieved from source via `congregate list`. If not, run `congregate list`
    """
    # List ALL source instance users/groups/projects if empty or not recent
    if not is_recent_file(
            "{}/data/projects.json".format(b.app_path), age=3600):
        list_data()
