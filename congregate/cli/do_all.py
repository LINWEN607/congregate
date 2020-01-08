from congregate.cli import stage_projects
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration import migrate
from congregate.helpers import base_module as b

users = UsersClient()
groups = GroupsClient()


def do_all(dry_run=True):
    # Stage
    stage_projects.stage_projects([None, "all"], dry_run)

    # Remove blocked users
    if not b.config.keep_blocked_users:
        users.remove_blocked_users(dry_run)

    # Update and map users
    users.update_staged_user_info(dry_run)
    users.map_new_users_to_groups_and_projects(dry_run)

    # Migrate
    migrate.migrate(dry_run)


def do_all_users(dry_run=True):
    # Stage
    stage_projects.stage_projects([None, "all"], dry_run)

    # Remove blocked users
    if not b.config.keep_blocked_users:
        users.remove_blocked_users(dry_run)

    # Migrate
    migrate.migrate(
        dry_run=dry_run,
        # skip_groups=True,
        skip_project_import=True,
        skip_project_export=True)

    # Output user migration stats


def do_all_groups_and_projecsts(dry_run=True):
    # Stage
    stage_projects.stage_projects([None, "all"], dry_run)

    # Remove blocked users
    if not b.config.keep_blocked_users:
        users.remove_blocked_users(dry_run)

    # Update and map users - handle NOT found users
    users.update_staged_user_info(dry_run)
    users.map_new_users_to_groups_and_projects(dry_run)

    # Migrate
    migrate.migrate(
        dry_run=dry_run,
        skip_users=True)


def do_all_new(dry_run=True):
    do_all_users(dry_run)

    # If there are no NOT founs users continue
    do_all_groups_and_projecsts(dry_run)
