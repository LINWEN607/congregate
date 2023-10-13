import os
from pathlib import Path
from celery import group, chain, chunks
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
    payload = BulkImportPayload(**request.json)
    dest_host = ""
    dest_token = ""
    dt_client = BulkImportsClient(payload.configuration.url, payload.configuration.access_token, dest_host, dest_token)
    dt_id, dt_entities = dt_client.trigger_bulk_import(payload)
    result = group(
        watch_import_status(dest_host, dest_token, dt_id),
        watch_import_entity_status.chunks(dt_entities, 1)
    )
    return jsonify({
        'status': 'triggered direct transfer jobs',
        'task_id': result.id
    }), 201


    
