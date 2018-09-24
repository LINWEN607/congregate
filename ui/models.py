import os
import json
from . import app
from flask import request, jsonify
from congregate.cli import stage_projects
from congregate.cli.config import update_config
from congregate.migration.groups import append_groups
from congregate.migration.users import append_users
from congregate.migration.projects import migrate

app_path = os.getenv("CONGREGATE_PATH")

def get_data(file_name):
    with open("%s/data/%s.json" % (app_path, file_name), "r") as f:
        return json.load(f)

@app.route("/data/<name>")
def load_stage_data(name):
    data = get_data(name)
    return jsonify(data)

@app.route("/stage", methods=['POST'])
def stage():
    projects = request.get_data().split(",")
    stage_projects.stage_projects(projects)
    return "staged %s projects" % len(projects)

@app.route("/append_users", methods=['POST'])
def add_users():
    users = request.get_data().split(",")
    append_users(users)
    return "added %s users" % len(users)

@app.route("/append_groups", methods=['POST'])
def add_groups():
    groups = request.get_data().split(",")
    append_groups(groups)
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