import json

from congregate.cli import stage_projects
from congregate.cli.list_projects import list_projects
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration import migrate
from congregate.helpers import base_module as b
from congregate.helpers.misc_utils import is_non_empty_file, remove_dupes

users = UsersClient()
groups = GroupsClient()


def do_all_users(dry_run=True):
    # List projects if older than 1h
    if not is_non_empty_file("{}/data/project_json.json".format(b.app_path), age=3600):
        list_projects()

    # Clear staged projects and groups and stage only users
    stage_projects.stage_projects([""], dry_run=False)
    groups.append_groups([])
    with open("{}/data/users.json".format(b.app_path), "r") as u:
        with open("{}/data/staged_users.json".format(b.app_path), "w") as su:
            json.dump(remove_dupes(json.load(u)), su, indent=4)

    # Remove blocked users - NO dry run
    if not b.config.keep_blocked_users:
        users.remove_blocked_users(dry_run=False)

    # Lookup not found users BEFORE - NO dry run
    users.update_staged_user_info(dry_run=False)

    # Migrate
    migrate.migrate(
        dry_run=dry_run,
        skip_groups=True,
        skip_project_import=True,
        skip_project_export=True)

    # Lookup not found users AFTER - NO dry run
    users.update_staged_user_info(dry_run=False)


def do_all_groups_and_projects(dry_run=True):
    stage_and_update_all()

    # Migrate
    migrate.migrate(
        dry_run=dry_run,
        skip_users=True)


def do_all(dry_run=True):
    stage_and_update_all()

    # Migrate
    migrate.migrate(dry_run=dry_run)


def stage_and_update_all():
    # List projects if older than 1h
    if not is_non_empty_file("{}/data/project_json.json".format(b.app_path), age=3600):
        list_projects()

    # Stage users, groups and projects - NO dry run
    stage_projects.stage_projects(["all"], dry_run=False)

    # Remove blocked users - NO dry run
    if not b.config.keep_blocked_users:
        users.remove_blocked_users(dry_run=False)

    # Remove NOT found users and map IDs - NO dry run
    users_not_found = users.update_staged_user_info(dry_run=False)
    users.remove_users_not_found("stage", users_not_found)
    users.remove_users_not_found("staged_groups", users_not_found)
    users.map_new_users_to_groups_and_projects(dry_run=False)
