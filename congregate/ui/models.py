import json
from math import floor
from flask import jsonify, Blueprint, request
from gitlab_ps_utils.misc_utils import strip_netloc
from congregate.helpers.utils import get_congregate_path
from congregate.helpers.congregate_mdbc import mongo_connection
from congregate.ui import config

data_retrieval = Blueprint('data', __name__)

def get_data(file_name, sort_by=None):
    data = None
    with open(f"{get_congregate_path()}/data/{file_name}.json", "r") as f:
        data = json.load(f)

    if sort_by is not None:
        return sorted(data, key=lambda d: d[sort_by])

    return data

@mongo_connection
def get_mongo_data(asset_type, per_page=50, page=1, sort_by=None, mongo=None):
    
    skip = per_page*page if page > 1 else 0
    data = None
    collection = f"{asset_type}-{strip_netloc(config.source_host)}"
    total_count = mongo.db[collection].count_documents({})
    last_page = floor(total_count / per_page)
    data = list(mongo.safe_find(collection, limit=per_page, skip=skip, projection={'_id': False}))
    return {
        "last_page": last_page,
        "data": data
    }


@data_retrieval.route("/summary")
@mongo_connection
def get_counts(mongo=None):
    total_projects = mongo.db[f'projects-{strip_netloc(config.source_host)}'].count_documents({})
    total_users = mongo.db[f'users-{strip_netloc(config.source_host)}'].count_documents({})
    total_groups = mongo.db[f'groups-{strip_netloc(config.source_host)}'].count_documents({})
    staged_projects = get_data("staged_projects")
    staged_users = get_data("staged_users")
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
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    data = get_mongo_data(name, per_page=per_page, page=page)
    return jsonify(data)
