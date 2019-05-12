from helpers.base_class import BaseClass
from helpers import api
from requests.exceptions import RequestException
from urllib import quote_plus
import json

class ProjectsClient(BaseClass):
    def search_for_project(self, host, token, name):
        yield api.list_all(host, token, "projects?search=%s" % quote_plus(name))

    def get_project(self, id, host, token):
        return api.generate_get_request(host, token, "projects/%d" % id)

    def get_members(self, id, host, token):
        yield api.list_all(host, token, "projects/%d/members" % id)

    def add_member_to_group(self, id, host, token, member):
        return api.generate_post_request(host, token, "projects/%d/members" % id, json.dumps(member))

    def archive_project(self, host, token, id):
        return api.generate_post_request(host, token, "projects/%d/archive" % id, {}).json()

    def unarchive_project(self, host, token, id):
        return api.generate_post_request(host, token, "projects/%d/unarchive" % id, {}).json()

    def get_approvals(self, id, host, token):
        return api.generate_get_request(host, token, "projects/%d/approvals" % id).json()

    def set_approval_configuration(self, id, host, token, data):
        '''
            refer to https://docs.gitlab.com/ee/api/merge_request_approvals.html#change-configuration
            
            example payload:
            {
                "approvals_before_merge": 2,
                "reset_approvals_on_push": True,
                "disable_overriding_approvers_per_merge_request": False
            }
        '''
        return api.generate_post_request(host, token, "projects/%d/approvals" % id, data)

    
    def set_approvers(self, project_id, host, token, approver_ids, approver_group_ids):
        if not isinstance(approver_ids, list):
            approver_ids = [approver_ids]
        if not isinstance(approver_group_ids, list):
            approver_group_ids = [approver_group_ids]
        data = {
            approver_ids: approver_ids,
            approver_group_ids: approver_group_ids
        }
        return api.generate_post_request(host, token, "projects/%d/approvers" % project_id, data)

    def add_members(self, members, id):
        root_user_present = False
        for member in members:
            if member["id"] == self.config.parent_user_id:
                root_user_present = True
            new_member = {
                "user_id": member["id"],
                "access_level": member["access_level"]
            }

            try:
                api.generate_post_request(self.config.parent_host, self.config.parent_token, "projects/%d/members" % id, json.dumps(new_member))
            except RequestException, e:
                self.l.logger.error(e)
                self.l.logger.error("Member might already exist. Attempting to update access level")
                try:
                    api.generate_put_request(self.config.parent_host, self.config.parent_token, "projects/%d/members/%d?access_level=%d" % (id, member["id"], member["access_level"]), data=None)
                except RequestException, e:
                    self.l.logger.error(e)
                    self.l.logger.error("Attempting to update existing member failed")

        if not root_user_present:
            self.l.logger.info("removing root user from project")
            api.generate_delete_request(self.config.parent_host, self.config.parent_token, "projects/%d/members/%d" % (id, self.config.parent_user_id))