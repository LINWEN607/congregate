from flask import request, jsonify, Response, stream_with_context, send_from_directory
from . import app
import subprocess, os
from helpers.base_module import app_path
from cli import stage_projects
from cli.config import update_config
from migration.gitlab.groups import GroupsClient
from migration.gitlab.users import UsersClient
from migration.migrate import migrate

grp = GroupsClient()
usr = UsersClient()

@app.route('/log')
def generate_stream():
    def generate():
        last_line = ""
        while True:
            output = subprocess.check_output(['tail', '-n 1', '%s/log' % app_path])
            if output == last_line:
                yield ""
            else:
                last_line = output
                yield "<p>" + output.split("|")[-1] + "</p>"
            subprocess.call(['sleep', '1'])

    return Response(stream_with_context(generate()))

@app.route('/logLine')
def return_last_line():
    output = subprocess.check_output(['tail', '-n 1', '%s/log' % app_path])
    return output.split(":")[-1]

@app.route("/stage", methods=['POST'])
def stage():
    projects = request.get_data().split(",")
    stage_projects.stage_projects(projects)
    return "staged %s projects" % len(projects)

@app.route("/append_users", methods=['POST'])
def add_users():
    users = request.get_data().split(",")
    usr.append_users(users)
    return "added %s users" % len(users)

@app.route("/append_groups", methods=['POST'])
def add_groups():
    groups = request.get_data().split(",")
    grp.append_groups(groups)
    return "added %s groups" % len(groups)

@app.route("/update_config", methods=['POST'])
def update_config_post():
    config = request.get_data()
    update_config(config)
    return "Updated config"

@app.route("/migrate", methods=['GET'])
def migrate_projects_get():
    migrate()
    return "Migrated projects"