import json
from flask import jsonify, Blueprint
from congregate.helpers.utils import get_congregate_path

data_retrieval = Blueprint('data', __name__)

def get_data(file_name, sort_by=None):
    data = None
    with open(f"{get_congregate_path()}/data/{file_name}.json", "r") as f:
        data = json.load(f)

    if sort_by is not None:
        return sorted(data, key=lambda d: d[sort_by])

    return data

@data_retrieval.route("/summary")
def get_counts():
    total_projects = len(get_data("projects"))
    staged_projects = get_data("staged_projects")
    total_users = len(get_data("users"))
    staged_users = get_data("staged_users")
    total_groups = len(get_data("groups"))
    staged_groups = get_data("staged_groups")
    return jsonify({
        "Total Staged Projects": f"{len(staged_projects)}/{total_projects}",
        "Staged Projects": staged_projects,
        "Total Staged Groups": f"{len(staged_groups)}/{total_groups}",
        "Staged Groups": staged_groups,
        "Total Staged Users": f"{len(staged_users)}/{total_users}",
        "Staged Users": staged_users,
    })

@data_retrieval.route("/<name>")
def load_stage_data(name):
    data = get_data(name)
    return jsonify(data)
