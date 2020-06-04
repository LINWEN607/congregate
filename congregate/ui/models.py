import json
from flask import jsonify

# from congregate.helpers.configuration_validator import ConfigurationValidator
from . import app

# try:
from congregate.helpers.misc_utils import get_congregate_path
# except ImportError:
#     from cli import stage_projects
#     from cli.config import update_config
#     from congregate.migration.groups import append_groups
#     from congregate.migration.users import append_users
#     from congregate.migration.projects import migrate


def get_data(file_name, sort_by=None):
    data = None
    with open("%s/data/%s.json" % (get_congregate_path(), file_name), "r") as f:
        data = json.load(f)

    if sort_by is not None:
        return sorted(data, key=lambda d: d[sort_by])

    return data


# def get_config():
#     config = ConfigurationValidator()
#     return config.as_obj()

@app.route("/data/summary")
def get_counts():
    total_projects = len(get_data("project_json"))
    staged_projects = get_data("stage")
    total_users = len(get_data("users"))
    staged_users = get_data("staged_users")
    total_groups = len(get_data("groups"))
    staged_groups = get_data("staged_groups")
    return jsonify({
        "Total Staged Projects": "%s/%s" % (len(staged_projects), total_projects),
        "Staged Projects": staged_projects,
        "Total Staged Groups": "%s/%s" % (len(staged_groups), total_groups),
        "Staged Groups": staged_groups,
        "Total Staged Users": "%s/%s" % (len(staged_users), total_users),
        "Staged Users": staged_users,
    })


@app.route("/data/<name>")
def load_stage_data(name):
    data = get_data(name)
    return jsonify(data)
