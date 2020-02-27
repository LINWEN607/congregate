import subprocess
from flask import request, Response, stream_with_context

from congregate.helpers.misc_utils import get_congregate_path
from congregate.cli import stage_projects
from congregate.cli.config import update_config
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.migrate import migrate

from . import app

grp = GroupsClient()
usr = UsersClient()


@app.route('/log')
def generate_stream():
    def generate():
        last_line = ""
        while True:
            output = subprocess.check_output(
                ['tail', '-n 1', '%s/data/congregate.log' % get_congregate_path()])
            if output == last_line:
                yield ""
            else:
                last_line = output
                yield "<p>" + output.split("|")[-1] + "</p>"
            subprocess.call(['sleep', '1'])

    return Response(stream_with_context(generate()))


@app.route('/logLine')
def return_last_line():
    output = subprocess.check_output(
        ['tail', '-n 1', '%s/data/congregate.log' % get_congregate_path()])
    return output.split(":")[-1]


def message(obj, obj_type):
    num = len(obj)
    return "Staged {0} {1}{2}".format(
        num,
        obj_type,
        "s" if num > 1 or num == 0 else "")


@app.route("/stage", methods=['POST'])
def stage():
    projects = request.get_data().split(",")
    stage_projects.stage_projects(projects, dry_run=False)
    return message(projects, "project")


@app.route("/append_users", methods=['POST'])
def add_users():
    users = request.get_data().split(",")
    usr.append_users(users)
    return message(users, "user")


@app.route("/append_groups", methods=['POST'])
def add_groups():
    groups = request.get_data().split(",")
    grp.append_groups(groups)
    return message(groups, "group")


@app.route("/update_config", methods=['POST'])
def update_config_post():
    config = request.get_data()
    update_config(config)
    return "Updated config"


@app.route("/migrate", methods=['GET'])
def migrate_projects_get():
    migrate()
    return "Migrated projects"
