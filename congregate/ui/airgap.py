import os
from pathlib import Path
from flask import jsonify, Blueprint, request, redirect, current_app
from werkzeug.utils import secure_filename
from gitlab_ps_utils.misc_utils import safe_json_response
from gitlab_ps_utils.dict_utils import dig
from congregate.migration.gitlab.migrate import export_task, import_task
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.ui.auth import validate_project_token, validate_group_token
from congregate.ui.data_models.airgap_export_payload import AirgapExportPayload
from congregate.ui.data_models.airgap_import_payload import AirgapImportPayload
from congregate.ui.constants import ALLOWED_EXTENSIONS

airgap_routes = Blueprint('airgap', __name__)

@airgap_routes.route('/export', methods=['POST'])
@validate_project_token
def trigger_export():
    payload = AirgapExportPayload(**request.json)
    project = safe_json_response(ProjectsApi().get_project(payload.pid, payload.host, payload.token))
    project['namespace'] = dig(project, 'namespace', 'full_path')
    result = export_task.delay(project, payload.host, payload.token)
    return jsonify({
        'status': 'triggered export',
        'task_id': result.id
    }), 201

@airgap_routes.route('/import', methods=['POST'])
@validate_group_token
def trigger_import():
    formdata = request.form
    payload = AirgapImportPayload(host=formdata.get('host'), token=formdata.get('token'), gid=formdata.get('gid'))
    group = safe_json_response(GroupsApi().get_group(payload.gid, payload.host, payload.token))
    # check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({
            'error': 'No file in request'
        }), 400
    file = request.files['file']
    print(file.filename)
    print(allowed_file(file.filename))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        result = import_task.delay(upload_path, group, payload.host, payload.token)
        return jsonify({
            'status': 'triggered import',
            'task_id': result.id
        }), 201
    return jsonify({
        'error': 'Invalid file provided in request'
    }), 400

def allowed_file(filename):
    return '.' in filename and \
           ''.join(Path(filename).suffixes) in ALLOWED_EXTENSIONS