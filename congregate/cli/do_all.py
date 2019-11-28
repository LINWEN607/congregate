import os
from congregate.cli import config, stage_projects
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration import migrate
from congregate.helpers import base_module

app_path = base_module.app_path
config = base_module.config

def do_all(dry_run=True):
    users = UsersClient()
    groups = GroupsClient()

    # Gather info
    if not os.path.isfile("%s/data/users.json" % app_path):
        users.retrieve_user_info()
    if not os.path.isfile("%s/data/groups.json" % app_path):
        groups.retrieve_group_info(config.source_host, config.source_token)

    # Stage
    stage_projects.stage_projects([None, "all"])

    # Update and map users
    users.update_staged_user_info()
    users.map_new_users_to_groups_and_projects(dry_run)

    # Migrate
    migrate.migrate(dry_run)


if __name__ == "__main__":
    do_all()
