import os
import json
from . import app
from flask import jsonify

# try:
from helpers.base_module import app_path
# except ImportError:
#     from cli import stage_projects
#     from cli.config import update_config
#     from migration.groups import append_groups
#     from migration.users import append_users
#     from migration.projects import migrate


def get_data(file_name, sort_by=None):
    data = None
    with open("%s/data/%s.json" % (app_path, file_name), "r") as f:
        data = json.load(f)

    if sort_by is not None:
        return sorted(data, key=lambda d: d[sort_by])

    return data


def get_counts():
    total_projects = len(get_data("project_json"))
    staged_projects = len(get_data("stage"))
    total_users = len(get_data("users"))
    staged_users = len(get_data("staged_users"))
    total_groups = len(get_data("groups"))
    staged_groups = len(get_data("staged_groups"))
    return {
        "Staged Projects": "%s/%s" % (staged_projects, total_projects),
        "Staged Groups": "%s/%s" % (staged_groups, total_groups),
        "Staged Users": "%s/%s" % (staged_users, total_users)
    }


@app.route("/data/<name>")
def load_stage_data(name):
    data = get_data(name)
    return jsonify(data)
