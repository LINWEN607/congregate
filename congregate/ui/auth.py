from functools import wraps
from flask import request, jsonify
from gitlab_ps_utils.misc_utils import safe_json_response
from gitlab_ps_utils.api import GitLabApi
from congregate.ui.data_models.airgap_export_payload import AirgapExportPayload
from congregate.ui.data_models.airgap_import_payload import AirgapImportPayload
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi

def validate_project_token(func):
    """
        Checks to make sure the supplied project token is valid    
    
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

def validate_group_token(func):
    """
        Checks to make sure the supplied group token is valid    
    
        If not, return a 403
    """
    @wraps(func)
    def add_route(*args, **kwargs):
        try:
            formdata = request.form
            payload = AirgapImportPayload(host=formdata.get('host'), token=formdata.get('token'), gid=formdata.get('gid'))
            if safe_json_response(GroupsApi().get_group(payload.gid, payload.host, payload.token)):
                return func(*args, **kwargs)
            return jsonify({'error': "Unauthorized"}), 403
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except TypeError as e:
            return jsonify({'error': str(e)}), 400
    return add_route
