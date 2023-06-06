import os
from flask import jsonify, Blueprint, request, redirect
from werkzeug.utils import secure_filename
from gitlab_ps_utils.misc_utils import safe_json_response
from gitlab_ps_utils.dict_utils import dig
from congregate.migration.gitlab.migrate import export_task, import_task
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.ui.auth import validate_project_token, validate_group_token
from congregate.ui.data_models.airgap_export_payload import AirgapExportPayload
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
    payload = AirgapExportPayload(**request.json)
    project = safe_json_response(ProjectsApi().get_project(payload.pid, payload.host, payload.token))
    project['namespace'] = dig(project, 'namespace', 'full_path')

    # check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({
            'error': 'No file in request'
        }), 400
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    # if file.filename == '':
    #     flash('No selected file')
    #     return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(airgap_routes.config['UPLOAD_FOLDER'], filename))

    result = import_task.delay(project, payload.host, payload.token)
    return jsonify({
        'status': 'triggered import',
        'task_id': result.id
    }), 201

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS