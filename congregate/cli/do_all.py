import json

from congregate.cli import stage_projects
from congregate.cli.list_source import list_data
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration import migrate
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_recent_file, remove_dupes

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
    list_all()

    # Clear staged projects and groups and stage only users
    stage_projects.stage_projects([""], dry_run=False)
    groups.append_groups([])
    with open("{}/data/users.json".format(b.app_path), "r") as u:
        with open("{}/data/staged_users.json".format(b.app_path), "w") as su:
            json.dump(remove_dupes(json.load(u)), su, indent=4)

    migrate.migrate(
        dry_run=dry_run,
        skip_group_export=True,
        skip_group_import=True,
        skip_project_import=True,
        skip_project_export=True)

    # Lookup not found users AFTER - NO dry run
    users.search_for_staged_users()


def do_all_groups_and_projects(dry_run=True):
    """
        Stages all groups and projects and migrates them to the destination instance

        :param: dry_run (bool) If true, will write POST request payload to JSON files for review. If false, will conduct full group and project migration
    """
    list_all()

    # Stage ALL - NO dry run
    stage_projects.stage_projects(["all"], dry_run=False, skip_users=True)

    migrate.migrate(dry_run=dry_run, skip_users=True)


def do_all(dry_run=True):
    """
        Stages all users, groups, and projects and migrates them to the destination instance

        :param: dry_run (bool) If true, will write POST request payload to JSON files for review. If false, will conduct full migration
    """
    list_all()

    do_all_users(dry_run=dry_run)
    do_all_groups_and_projects(dry_run=dry_run)


def list_all():
    """
        Checks if data has been retrieved from source via `congregate list`. If not, run `congregate list`
    """
    # List ALL source instance users/groups/projects if empty or not recent
    if not is_recent_file(
            "{}/data/project_json.json".format(b.app_path), age=3600):
        list_data()
