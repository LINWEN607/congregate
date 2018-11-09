import os
import subprocess
from cli import config, stage_projects
from migration import users, groups
import migration.projects

app_path = os.getenv("CONGREGATE_PATH")

def do_all():
    if not os.path.isfile("%s/data/config.json" % app_path):
        config.config()
    if not os.path.isfile("%s/data/users.json" % app_path):
        users.retrieve_user_info()
    if not os.path.isfile("%s/data/groups.json" % app_path):
        groups.retrieve_group_info()
    stage_projects.stage_projects([None, "all"])
    projects.migrate()

if __name__ == "__main__":
    do_all()
