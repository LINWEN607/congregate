from dacite import from_dict
from celery import chain
from flask import jsonify, Blueprint, request

from congregate.ui.utils.decorators import enforce_dry_run
from congregate.helpers.celery_utils import get_task_status, find_arg_prop
from congregate.migration.gitlab.migrate import post_migration_task
from congregate.migration.gitlab.bulk_imports import BulkImportsClient, watch_import_entity_status, watch_import_status
from congregate.migration.meta.api_models.bulk_import import BulkImportPayload

direct_transfer_routes = Blueprint('direct_transfer', __name__)


@direct_transfer_routes.route('/import', methods=['POST'])
@enforce_dry_run
def trigger_direct_transfer(dry_run=True):
    payload = from_dict(data_class=BulkImportPayload, data=request.json)
    dt_client = BulkImportsClient(payload.configuration.url, payload.configuration.access_token)
    dt_id, dt_entities, errors = dt_client.trigger_bulk_import(payload, dry_run=dry_run)
    if dt_id and dt_entities:
        # Kick off overall watch job
        watch_status = watch_import_status.delay(dt_client.config.destination_host, dt_client.config.destination_token, dt_id)
        entity_ids = []
        for entity in dt_entities:
            # Chain together watching the status of a specific entity
            # and then once that job completes, trigger post migration tasks
            res = chain(
                watch_import_entity_status.s(dt_client.config.destination_host, dt_client.config.destination_token, entity), 
                post_migration_task.s(dt_client.config.destination_host, dt_client.config.destination_token, dry_run=dry_run)
            ).apply_async(queue='celery')
            entity_ids.append(res.id)
        return jsonify({
            'status': 'triggered direct transfer jobs',
            'overall_status_id': watch_status.id,
            'entity_ids': entity_ids 
        }), 201
    if dt_entities and (not dt_id):
        return jsonify({
            'status': 'dry run successful',
            'dry_run_data': dt_entities
        }), 200
    return jsonify({
        'status': 'failed to trigger direct transfer import',
        'message': errors
    }), 400

@direct_transfer_routes.route('/import-status/<id>', methods=['GET'])
def get_import_status(id):
    res = get_task_status(id)
    return jsonify({
        'task-id': id,
        'status': res.state,
        'task_name': res.name,
        'entity_name': find_arg_prop(res, 'destination_name')
    }), 200

