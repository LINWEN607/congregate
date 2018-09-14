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