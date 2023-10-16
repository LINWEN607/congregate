import os
from dacite import from_dict
from pathlib import Path
from celery import group, chain, shared_task
from flask import jsonify, Blueprint, request, redirect, current_app
from werkzeug.utils import secure_filename
from gitlab_ps_utils.misc_utils import safe_json_response
from gitlab_ps_utils.dict_utils import dig

from congregate.ui.auth import validate_project_token, validate_group_token
from congregate.migration.gitlab.migrate import post_migration_task
from congregate.migration.gitlab.bulk_imports import BulkImportsClient, watch_import_entity_status, watch_import_status
from congregate.migration.meta.api_models.bulk_import import BulkImportPayload

direct_transfer_routes = Blueprint('direct_transfer', __name__)

@direct_transfer_routes.route('/import', methods=['POST'])
def trigger_direct_transfer():
    payload = from_dict(data_class=BulkImportPayload, data=request.json)
    dt_client = BulkImportsClient(payload.configuration.url, payload.configuration.access_token)
    dt_id, dt_entities, errors = dt_client.trigger_bulk_import(payload)
    if dt_id and dt_entities:
        watch_import_status.delay(dt_client.config.destination_host, dt_client.config.destination_token, dt_id)
        for entity in dt_entities:
            res = chain(watch_import_entity_status.s(dt_client.config.destination_host, dt_client.config.destination_token, entity), 
                post_migration_task.s(dt_client.config.destination_host, dt_client.config.destination_token)).apply_async(queue='celery')
            print(res.id)
        return jsonify({
            'status': 'triggered direct transfer jobs',
            'task_id': 1234
        }), 201
    return jsonify({
        'status': 'failed to trigger direct transfer import',
        'message': errors
    }), 400

