from dacite import from_dict
from flask import jsonify, Blueprint, request

from congregate.helpers.migrate_utils import get_staged_groups, get_staged_projects
from congregate.ui.utils.decorators import enforce_dry_run
from congregate.helpers.celery_utils import get_task_status, find_arg_prop
from congregate.helpers.celery_mdbc import mongo_connection
from congregate.migration.gitlab.bulk_imports import BulkImportsClient, kick_off_bulk_import
from congregate.migration.meta.api_models.bulk_import import BulkImportPayload

direct_transfer_routes = Blueprint('direct_transfer', __name__)


@direct_transfer_routes.route('/import', methods=['POST'])
@enforce_dry_run
def trigger_direct_transfer(dry_run=True):
    payload = from_dict(data_class=BulkImportPayload, data=request.json)
    return trigger_migration(payload, dry_run=dry_run)

@direct_transfer_routes.route('/migrate/<entity_type>', methods=['POST'])
@enforce_dry_run
def trigger_staged_migration(entity_type, dry_run=True):
    dt_client = BulkImportsClient()
    payload = None
    if entity_type == 'groups':
        data = get_staged_groups()
        payload = dt_client.build_payload(data, 'group')
    elif entity_type == 'projects':
        data = get_staged_projects()
        payload = dt_client.build_payload(data, 'project')
    return trigger_migration(payload, dry_run=dry_run)

@direct_transfer_routes.route('/import-status/<id>', methods=['GET'])
def get_import_status(id):
    res = get_task_status(id)
    return jsonify({
        'task-id': id,
        'status': res.state,
        'task_name': res.name,
        'entity_name': find_arg_prop(res, 'destination_name'),
        'result': res.result
    }), 200

@direct_transfer_routes.route('/migration-status', methods=['GET'])
def get_migration_status():
    response = []
    for pending_task in find_pending_migration_tasks():
        task_status = get_task_status(pending_task.get('_id'))
        response.append({
            'task_id': pending_task.get('_id'),
            'status': task_status.state,
            'task_name': pending_task.get('task'),
            'entity_name': find_arg_prop(task_status, 'destination_name')
        })
    return jsonify(response), 200

def trigger_migration(payload: BulkImportPayload, dry_run=True):
    entrypoint_task = kick_off_bulk_import.delay(payload.to_dict(), dry_run=dry_run)
    return jsonify({
        'status': 'Started migration',
        'task_id': entrypoint_task.id
    }), 201

@mongo_connection
def find_pending_migration_tasks(mongo=None):
    migration_tasks = [
        'trigger-bulk-import-task',
        'watch-import-status',
        'watch-import-entity-status',
        'post-migration-task'
    ]
    return mongo.safe_find('celery_taskmeta', {
        'task': {
            '$in': migration_tasks
        }, 
        'status': {
            '$in': ['PENDING', 'STARTED']
        }
    })


