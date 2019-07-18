import os
from congregate.cli import config, stage_projects
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration import migrate
from congregate.helpers import base_module

app_path = base_module.app_path
config = base_module.config

def do_all():
    users = UsersClient()
    groups = GroupsClient()
    # if not os.path.isfile("%s/data/config.json" % app_path):
    #     config.config()
    if not os.path.isfile("%s/data/users.json" % app_path):
        users.retrieve_user_info()
    if not os.path.isfile("%s/data/groups.json" % app_path):
        groups.retrieve_group_info(config.child_host, config.child_token)
    stage_projects.stage_projects([None, "all"])
    migrate.migrate()


if __name__ == "__main__":
    do_all()
