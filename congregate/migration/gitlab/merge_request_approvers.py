from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.migration.gitlab.version import VersionClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.groups import GroupsClient
from urllib import urlencode
import json


class MergeRequestApproversClient(BaseClass):
    def __init__(self):
        self.version = VersionClient()
        self.users = UsersClient()
        self.groups = GroupsClient()
        self.break_change_version = "11.10.0"
        super(MergeRequestApproversClient, self).__init__()

    def get_approvals(self, id, host, token):
        version = self.version.get_version(host, token)
        if self.version.is_older_than(version["version"], self.break_change_version):
            return api.generate_get_request(host, token, "projects/%d/approvals" % id).json()
        else:
            return api.generate_get_request(host, token, "projects/%d/approval_settings" % id).json()

    def set_approval_configuration(self, id, host, token, data):
        '''
            refer to https://docs.gitlaself.com/ee/api/merge_request_approvals.html#change-configuration

            example payload:
            {
                "approvals_before_merge": 2,
                "reset_approvals_on_push": True,
                "disable_overriding_approvers_per_merge_request": False
            }
        '''
        return api.generate_post_request(host, token, "projects/%d/approvals?%s" % (id, urlencode(data)), None)

    def set_approvers(self, project_id, host, token, approver_ids, approver_group_ids):
        if not isinstance(approver_ids, list):
            approver_ids = [approver_ids]
        if not isinstance(approver_group_ids, list):
            approver_group_ids = [approver_group_ids]
        data = {
            "approver_ids": approver_ids,
            "approver_group_ids": approver_group_ids
        }
        return api.generate_put_request(host, token, "projects/%d/approvers?%s" % (project_id, urlencode(data)), None)

    def create_approval_rule(self, project_id, host, token, rule_name, approvals_required, approver_ids, approver_group_ids):
        data = {
            "name": rule_name,
            "approvals_required": approvals_required,
            "users": approver_ids,
            "groups": approver_group_ids
        }
        return api.generate_post_request(host, token, "projects/%d/approval_settings/rules" % project_id, json.dumps(data))

    def create_approval_rule_with_payload(self, project_id, host, token, data):
        return api.generate_post_request(host, token, "projects/%d/approval_settings/rules" % project_id, json.dumps(data))

    def migrate_merge_request_approvers(self, new_id, old_id):
        approval_data = self.get_approvals(
            old_id, self.config.source_host, self.config.source_token)
        source_version = self.version.get_version(
            self.config.source_host, self.config.source_token)["version"]
        destination_version = self.version.get_version(
            self.config.destination_host, self.config.destination_token)["version"]

        if self.version.is_older_than(destination_version, self.break_change_version):
            if self.version.is_older_than(source_version, self.break_change_version):
                approver_ids, approver_groups = self.update_mr_approvers_old(
                    new_id, approval_data)
                self.set_approvers(old_id, self.config.destination_host,
                                   self.config.destination_token, approver_ids, approver_groups)
        else:
            if self.version.is_older_than(source_version, self.break_change_version):
                approver_ids, approver_groups = self.update_mr_approvers_old(
                    new_id, approval_data)
                self.create_approval_rule(
                    new_id, self.config.destination_host, self.config.destination_token, "Default", approval_data["approvals_before_merge"], approver_ids, approver_groups)
            else:
                for new_rule in self.update_mr_approvers_new(new_id, approval_data):
                    created_rule_resp = self.create_approval_rule_with_payload(
                        new_id, self.config.destination_host, self.config.destination_token, new_rule)

    def update_approvers(self, approval_data):
        approver_ids = []
        approver_groups = []
        for approved_user in approval_data["approvers"]:
            user = approved_user["user"]
            if user.get("id", None) is not None:
                user = self.users.get_user(
                    user["id"], self.config.source_host, self.config.source_token).json()
                new_user = api.search(
                    self.config.destination_host, self.config.destination_token, 'users', user['email'])
                new_user_id = new_user[0]["id"]
                approver_ids.append(new_user_id)
        for approved_group in approval_data["approver_groups"]:
            group = approved_group["group"]
            if group.get("id", None) is not None:
                group = self.groups.get_group(
                    group["id"], self.config.source_host, self.config.source_token).json()
                if self.config.parent_id is not None:
                    parent_group = self.groups.get_group(
                        self.config.parent_id, self.config.destination_host, self.config.destination_token).json()
                    group["full_path"] = "%s/%s" % (
                        parent_group["full_path"], group["full_path"])
                for new_group in self.groups.search_for_group(group["name"], self.config.destination_host, self.config.destination_token):
                    if new_group["full_path"].lower() == group["full_path"].lower():
                        approver_groups.append(new_group["id"])
                        break
        return approver_ids, approver_groups

    def update_approver_rule(self, rule):
        approver_ids = []
        approver_groups = []
        for user in rule["users"]:
            if user.get("id", None) is not None:
                user = self.users.get_user(
                    user["id"], self.config.source_host, self.config.source_token).json()
                new_user = api.search(
                    self.config.destination_host, self.config.destination_token, 'users', user['email'])
                new_user_id = new_user[0]["id"]
                approver_ids.append(new_user_id)
        for group in rule["groups"]:
            if group.get("id", None) is not None:
                group = self.groups.get_group(
                    group["id"], self.config.source_host, self.config.source_token).json()
                if self.config.parent_id is not None:
                    parent_group = self.groups.get_group(
                        self.config.parent_id, self.config.destination_host, self.config.destination_token).json()
                    group["full_path"] = "%s/%s" % (
                        parent_group["full_path"], group["full_path"])
                for new_group in self.groups.search_for_group(group["name"], self.config.destination_host, self.config.destination_token):
                    if new_group["full_path"].lower() == group["full_path"].lower():
                        approver_groups.append(new_group["id"])
                        break
        return approver_ids, approver_groups

    def update_mr_approvers_old(self, new_id, approval_data):
        approval_configuration = {
            "approvals_before_merge": approval_data["approvals_before_merge"],
            "reset_approvals_on_push": approval_data["reset_approvals_on_push"],
            "disable_overriding_approvers_per_merge_request": approval_data["disable_overriding_approvers_per_merge_request"]
        }
        self.set_approval_configuration(
            new_id, self.config.destination_host, self.config.destination_token, approval_configuration)

        return self.update_approvers(approval_data)

    def update_mr_approvers_new(self, new_id, approval_data):
        for rule in approval_data["rules"]:
            approver_rule_ids, approver_rule_groups = self.update_approver_rule(
                rule)
            yield {
                "name": rule["name"],
                "approvals_required": rule["approvals_required"],
                "users": approver_rule_ids,
                "groups": approver_rule_groups
            }
