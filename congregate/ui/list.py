from os.path import getmtime
from datetime import datetime
from flask import request, jsonify
from flask import Blueprint
from celery import states
from gitlab_ps_utils.misc_utils import strip_netloc
from congregate.helpers.congregate_mdbc import mongo_connection as congregate_mongo_connection
from congregate.helpers.celery_mdbc import mongo_connection as celery_mongo_connection
from congregate.helpers.utils import get_congregate_path
from congregate.helpers.celery_utils import get_task_status
from congregate.cli.list_source import list_data as list_data_task
from congregate.ui import config

list_functions = Blueprint('simple_page', __name__,
                        template_folder='templates')

@list_functions.route('/list', methods=['POST'])
def list_data():
    data = request.get_json()
    res = list_data_task.delay(
        partial=data.get('partial', False),
        skip_users=data.get('skip_users', False),
        skip_groups=data.get('skip_groups', False),
        skip_group_members=data.get('skip_group_members', False),
        skip_projects=data.get('skip_projects', False),
        skip_project_members=data.get('skip_project_members', False),
        skip_ci=data.get('skip_ci', False),
        src_instances=data.get('src_instances', False),
        subset=data.get('subset', False)
    )
    return jsonify({
        'task-id': res.id,
        'status': 'Successfully triggered list request'
    })

@list_functions.route('/list-status/<id>', methods=['GET'])
def get_list_status(id):
    users, groups, projects = get_counts()
    finished_states = [states.FAILURE, states.REVOKED, states.SUCCESS]
    if res := get_task_by_id(id):
        if parent := res.get('parent_id'):
            res = get_task_status(parent)
        else:
            res = get_task_status(id)
            if res.state in [states.FAILURE, states.REVOKED]:
                return jsonify(
                    task_status_response(res.id, res.state, res.name, res.result, users, groups, projects)
                ), 200
        if res.children:
            child_not_finished = False
            for child in res.children:
                if child.state not in finished_states:
                    child_not_finished = True
            if child_not_finished or (res.state not in finished_states):
                state = states.PENDING
            else:
                state = res.state
        else:
            state = states.PENDING
        return jsonify(
            task_status_response(res.id, state, res.name, res.result, users, groups, projects)
        ), 200
    return jsonify(
        task_status_response(id, states.PENDING, None, None, users, groups, projects)
    ), 200

@list_functions.route('/last-list', methods=['GET'])
def get_last_list_date():
    try:
        last_modified_date = str(datetime.fromtimestamp(getmtime(f"{get_congregate_path()}/data/projects.json")))
    except FileNotFoundError:
        last_modified_date = None
    return jsonify({
        'last-modified-date': last_modified_date
    })

@list_functions.route('/dump-list-data', methods=['POST'])
@congregate_mongo_connection
def dump_list_data(mongo=None):
    mongo.dump_collection_to_file(f"users-{strip_netloc(config.source_host)}", f"{get_congregate_path()}/data/users.json"),
    mongo.dump_collection_to_file(f"groups-{strip_netloc(config.source_host)}", f"{get_congregate_path()}/data/groups.json"),
    mongo.dump_collection_to_file(f"projects-{strip_netloc(config.source_host)}", f"{get_congregate_path()}/data/projects.json")
    return jsonify({
        'message': 'successfully dumped listed data'
    }), 200

@celery_mongo_connection
def get_task_by_id(id, mongo=None):
    return mongo.safe_find_one('celery_taskmeta', {"_id": id})

@congregate_mongo_connection
def get_counts(mongo=None):
    users = mongo.db[f"users-{strip_netloc(config.source_host)}"].count_documents({}) or 0
    groups = mongo.db[f"groups-{strip_netloc(config.source_host)}"].count_documents({}) or 0
    projects = mongo.db[f"projects-{strip_netloc(config.source_host)}"].count_documents({}) or 0
    return (users, groups, projects)

def task_status_response(id, status, task_name, result, users, groups, projects):
    return {
        'task-id': id,
        'status': status,
        'task_name': task_name,
        'result': result,
        'counts': {
            'projects': projects,
            'groups': groups,
            'users': users
        }
    }
