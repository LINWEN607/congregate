from functools import wraps
from flask import request, jsonify
from gitlab_ps_utils.misc_utils import safe_json_response
from gitlab_ps_utils.api import GitLabApi
from congregate.ui.data_models.airgap_export_payload import AirgapExportPayload
from congregate.migration.gitlab.api.projects import ProjectsApi

def validate_project_token(func):
    """
        Decorates a route as unauthorized by adding the unauthorized route
        to a list of endpoints, and then checks if the requesting IP
        is in the app's IP allowlist

        If the requesting IP is in the allowlist, return the decorated function
        If not, return a 403
    """
    @wraps(func)
    def add_route(*args, **kwargs):
        try:
            payload = AirgapExportPayload(**request.json)
            if safe_json_response(ProjectsApi().get_project(payload.pid, payload.host, payload.token)):
                return func(*args, **kwargs)
            return jsonify({'error': "Unauthorized"}), 403
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except TypeError as e:
            return jsonify({'error': str(e)}), 400
    return add_route
