from flask import jsonify, Blueprint, request
from gitlab_ps_utils.misc_utils import safe_json_response
from gitlab_ps_utils.dict_utils import dig
from congregate.migration.gitlab.migrate import export_task
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.ui.auth import validate_project_token
from congregate.ui.data_models.airgap_export_payload import AirgapExportPayload

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
