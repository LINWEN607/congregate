#!/bin/bash

# Congregate - GitLab instance migration utility 
#
# Copyright (c) 2018 - GitLab
#
# Master script for running congregate
#

import os, sys, subprocess
from helpers import conf
from migration import users, groups, projects
from cli import list_projects, stage_projects, do_all

app_path = os.getenv("CONGREGATE_PATH")
config = conf.ig()

if not os.path.isfile("%s/data/config.json" % app_path):
    config.config()

arg = sys.argv[1]

cmd_args = sys.argv[2:]

if arg == "list":
    list_projects.list_projects()
elif arg == "config":
    config.config()
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
    current_dir = os.getcwd()
    os.environ["FLASK_APP"] = "%s/ui" % app_path
    os.chdir(app_path)
    run_ui = "pipenv run flask run"
    subprocess.call(run_ui.split(" "))
