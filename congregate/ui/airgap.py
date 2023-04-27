from flask import jsonify, Blueprint, request
from congregate.migration.gitlab.migrate import GitLabMigrateClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.ui.auth import validate_project_token
from congregate.ui.data_models.airgap_export_payload import AirgapExportPayload

airgap_routes = Blueprint('data', __name__)

@airgap_routes.route('/export', methods=['POST'])
@validate_project_token
def trigger_export():
    payload = AirgapExportPayload(**request.json)
    project = ProjectsApi().get_project(payload.pid, payload.host, payload.token)
    client = GitLabMigrateClient(dry_run=False, skip_users=True, 
                           skip_groups=True, skip_project_import=True)
    client.handle_exporting_projects(project)
    return jsonify({
        'status': 'triggered export'
    }), 201
    