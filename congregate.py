#!/bin/bash

# Congregate - GitLab instance migration utility 
#
# Copyright (c) 2018 - GitLab
#
# Master script for running congregate
#

import os, sys, subprocess
from helpers import conf
from helpers import logger as log
try:
    from migration import users, groups, projects
except ImportError:
    import migration.users, migration.groups, migration.projects
from cli import list_projects, stage_projects, do_all
from cli import config as configure

app_path = os.getenv("CONGREGATE_PATH")

l = log.congregate_logger(__name__)

config = conf.ig()

if not os.path.isfile("%s/data/config.json" % app_path):
    config.config()

arg = sys.argv[1]

cmd_args = sys.argv[2:]

if arg == "list":
    list_projects.list_projects()
elif arg == "config":
    configure.config()
elif arg == "stage":
    stage_projects.stage_projects(cmd_args)
elif arg == "migrate":
    projects.migrate()
elif arg == "retrieve-groups":
    groups.retrieve_group_info()
elif arg == "retrieve-users":
    users.retrieve_user_info()
elif arg == "do_all":
    do_all.do_all()
elif arg == "ui":
    os.environ["FLASK_APP"] = "%s/ui" % app_path
    os.chdir(app_path)
    os.environ["PYTHONPATH"] = app_path
    run_ui = "pipenv run flask run --host=0.0.0.0"
    subprocess.call(run_ui.split(" "))
elif arg == "update-user-info":
    users.update_user_after_migration()
elif arg == "update-new-users":
    users.update_user_info_separately()
elif arg == "add-users-to-parent-group":
    users.add_users_to_parent_group()
elif arg == "remove-blocked-users":
    users.remove_blocked_users()
elif arg == "change-group-permissions":
    users.lower_user_permissions()
elif arg == "import_projects":
    projects.kick_off_import()
elif arg == "get-total-count":
    print projects.get_total_migrated_count()
elif arg == "find_unimported_projects":
    projects.find_unimported_projects()
elif arg == "dedupe":
    projects.dedupe_imports()
elif arg == "stage_unimported_projects":
    projects.stage_unimported_projects()
elif arg == "remove-users-from-parent":
    users.remove_users_from_parent_group()
elif arg == "migrate_variables_in_stage":
    projects.migrate_variables_in_stage()
elif arg == "remove_all_mirrors":
    projects.remove_all_mirrors()
elif arg == "find_all_internal_projects":
    groups.find_all_internal_projects()
elif arg == "make_all_internal_groups_private":
    groups.make_all_internal_groups_private()
elif arg == "check_visibility":
    projects.check_visibility()
elif arg == "update_group_members":
    groups.update_members()
elif arg == "enable-mirror":
    projects.enable_mirror()
