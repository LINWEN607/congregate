import json
from flask import jsonify

# from congregate.helpers.configuration_validator import ConfigurationValidator
from . import app

# try:
from congregate.helpers.utils import get_congregate_path
# except ImportError:
#     from cli import stage_projects
#     from cli.config import update_config
#     from congregate.migration.groups import append_groups
#     from congregate.migration.users import append_users
#     from congregate.migration.projects import migrate


def get_data(file_name, sort_by=None):
    data = None
    with open(f"{get_congregate_path()}/data/{file_name}.json", "r") as f:
        data = json.load(f)

    if sort_by is not None:
        return sorted(data, key=lambda d: d[sort_by])

    return data


# def get_config():
#     config = ConfigurationValidator()
#     return config.as_obj()

@app.route("/data/summary")
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


@app.route("/data/<name>")
def load_stage_data(name):
    data = get_data(name)
    return jsonify(data)
