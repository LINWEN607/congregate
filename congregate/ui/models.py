import json
from math import ceil
from flask import jsonify, Blueprint, request
from gitlab_ps_utils.misc_utils import strip_netloc
from congregate.helpers.utils import get_congregate_path
from congregate.helpers.congregate_mdbc import mongo_connection
from congregate.ui import config

data_retrieval = Blueprint('data', __name__)

USER_SEARCH_KEYS = ['id', 'name', 'username', 'email', 'state']
GROUP_SEARCH_KEYS = ['id', 'name', 'visibility', 'full_path']
PROJECT_SEARCH_KEYS = ['id', 'name', 'path_with_namespace', 'visibility', 'archived']

def get_data(file_name, sort_by=None):
    data = None
    with open(f"{get_congregate_path()}/data/{file_name}.json", "r") as f:
        data = json.load(f)

    if sort_by is not None:
        return sorted(data, key=lambda d: d[sort_by])

    return data

@mongo_connection
def get_mongo_data(asset_type, per_page=50, page=1, sort_by=None, projection=None, filter=None, mongo=None):
    """
        Retrieves data from mongo based on parameters supplied by the UI
    """
    skip = per_page*(page-1) if page > 1 else 0
    data = None
    query = None
    collection = f"{asset_type}-{strip_netloc(config.source_host)}"
    total_count = mongo.db[collection].count_documents({})
    if per_page:
        last_page = ceil(total_count / per_page)
    else:
        last_page = 0
    if not projection:
        # explicitly strip out the object ids since they are not JSON serializable
        projection = {'_id': False}
    if filter:
        if matching_ids := filter_results(asset_type, collection, filter):
            last_page = ceil(len(matching_ids) / per_page)
            query = {"_id": {"$in": matching_ids}}
    data = list(mongo.safe_find(collection, limit=per_page, skip=skip, projection=projection, query=query))
    return {
        "last_page": last_page,
        "data": data
    }

@mongo_connection
def filter_results(asset_type, collection, filter, mongo=None):
    """
        Filter the results of the mongo search based on terms provided by UI

        This is a workaround to MongoDB not supporting a partial search when using a text index.
        This returns all documents in a collection and only includes the fields we want to filter against.
        Once we have the results, we do a basic 'term in key-value' check and append the _id to filtered_results
    """
    asset_type_fields = {
        "projects": PROJECT_SEARCH_KEYS,
        "users": USER_SEARCH_KEYS,
        "groups": GROUP_SEARCH_KEYS,
    }
    fields = asset_type_fields.get(asset_type, [])
    projection = {field: True for field in fields}
    filtered_results = set()
    for result in list(mongo.safe_find(collection, projection=projection)):
        for val in result.values():
            if filter.lower() in str(val).lower():
                filtered_results.add(result['_id'])
                continue
    return list(filtered_results)



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
def load_data(name):
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    filter = request.args.get('filter_by', '')
    data = get_mongo_data(name, per_page=per_page, page=page, filter=filter)
    return jsonify(data)

@data_retrieval.route("/staged/<name>")
def get_all_staged_data(name):
    # Holding off pulling data from mongo
    # data = get_mongo_data(name, per_page=0, page=0, projection={'_id': False, "id": True})
    # as_list = [d['id'] for d in data['data']]
    # return jsonify(as_list)
    return jsonify(get_data(f"staged_{name}"))
