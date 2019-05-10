from helpers.base_class import base_class
from helpers import api

class gl_projects_client(base_class):
    def archive_project(self, host, token, id):
        return api.generate_post_request(host, token, "projects/%d/archive" % id, {}).json()

    def unarchive_project(self, host, token, id):
        return api.generate_post_request(host, token, "projects/%d/unarchive" % id, {}).json()

    def get_approvals(self, id, host, token):
        return api.generate_get_request(host, token, "projects/%d/approvals" % id).json()
    
    def set_approvals(self, project_id, host, token, approver_ids, approver_group_ids):
        if not isinstance(approver_ids, list):
            approver_ids = [approver_ids]
        if not isinstance(approver_group_ids, list):
            approver_group_ids = [approver_group_ids]
        data = {
            approver_ids: approver_ids,
            approver_group_ids: approver_group_ids
        }
        return api.generate_post_request(host, token, "projects/%d/approvers" % project_id, data)