import os
from cli import config, stage_projects
from migration.gitlab.users import gl_users_client 
from migration.gitlab.groups import gl_groups_client
from migration import migrate
from helpers.base_module import app_path

def do_all():
    users = gl_users_client()
    groups = gl_groups_client()
    if not os.path.isfile("%s/data/config.json" % app_path):
        config.config()
    if not os.path.isfile("%s/data/users.json" % app_path):
        users.retrieve_user_info()
    if not os.path.isfile("%s/data/groups.json" % app_path):
        groups.retrieve_group_info()
    stage_projects.stage_projects([None, "all"])
    migrate.migrate()

if __name__ == "__main__":
    do_all()
