from flask import jsonify, Blueprint

from congregate.helpers.celery_mdbc import mongo_connection
from congregate.ui.data_models.job_task_status import JobTaskResponse

job_queue_routes = Blueprint('jobs', __name__)

@job_queue_routes.route('/status/<status>')
def jobs_by_status(status):
    return jsonify(get_jobs_by_status(status)), 200

@job_queue_routes.route('/status/<status>/count')
def job_count_by_status(status):
    return jsonify(get_job_count_by_status(status)), 200

@job_queue_routes.route('/name/<name>')
def jobs_by_name(name):
    return jsonify(get_jobs_by_name(name)), 200

@mongo_connection
def get_jobs_by_status(status, mongo=None):
    tasks = []
    pending_jobs = list(mongo.find_tasks_by_status(status.upper()))

    for job in pending_jobs:
        tasks.append(JobTaskResponse(
            id=job['_id'],
            name=job['task'],
            status=job['status']
        ).to_dict())
    return tasks

@mongo_connection
def get_job_count_by_status(status, mongo=None):
    tasks_by_type = {}
    pending_jobs = list(mongo.find_tasks_by_status(status.upper()))

    for job in pending_jobs:
        if tasks_by_type.get(job['task']):
            tasks_by_type[job['task']] += 1
        else:
            tasks_by_type[job['task']] = 1

    return tasks_by_type

@mongo_connection
def get_jobs_by_name(name, mongo=None):
    tasks = []
    for task in list(mongo.find_tasks_by_name(name)):
        tasks.append(JobTaskResponse(
            id=task['_id'],
            name=task['task'],
            status=task['status']
        ).to_dict())
    return tasks

