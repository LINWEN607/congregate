import os
import json
from . import app
from flask import request, jsonify
from congregate.cli import stage_projects

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

def get_counts():
    total_projects = len(get_data("project_json"))
    staged_projects = len(get_data("stage"))
    total_users = len(get_data("users"))
    staged_users = 0
    total_groups = len(get_data("groups"))
    staged_groups = 0
    return {
        "Staged Projects": "%s/%s" % (staged_projects, total_projects),
        "Staged Groups": "%s/%s" % (staged_groups, total_groups),
        "Staged Users": "%s/%s" % (staged_users, total_users)
    }