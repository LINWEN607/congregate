import json

from urllib import urlencode
from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.migration.gitlab.version import VersionClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.users import UsersApi


class MergeRequestApproversClient(BaseClass):
    def __init__(self):
        self.version = VersionClient()
        self.users_api = UsersApi()
        self.groups_api = GroupsApi()
        self.projects_api = ProjectsApi()
        self.break_change_version = "11.10.0"
        super(MergeRequestApproversClient, self).__init__()

    def are_enabled(self, id):
        project = self.projects_api.get_project(id, self.config.source_host, self.config.source_token).json()
        return project.get("merge_requests_enabled", False)

    def get_approvals(self, id, host, token):
        version = self.version.get_version(host, token)
        if self.version.is_older_than(version["version"], self.break_change_version):
            return self.projects_api.get_all_project_approval_configuration(id, host, token).json()
        else:
            return self.projects_api.get_all_project_approval_settings(id, host, token).json()

    def set_approvers(self, project_id, host, token, approver_ids, approver_group_ids):
        if not isinstance(approver_ids, list):
            approver_ids = [approver_ids]
        if not isinstance(approver_group_ids, list):
            approver_group_ids = [approver_group_ids]
        data = {
            "approver_ids": approver_ids,
            "approver_group_ids": approver_group_ids
        }
        return self.projects_api.set_approvers(project_id, host, token, data)

    def create_approval_rule(self, project_id, host, token, rule_name, approvals_required, approver_ids, approver_group_ids):
        data = {
            "name": rule_name,
            "approvals_required": approvals_required,
            "users": approver_ids,
            "groups": approver_group_ids
        }
        return self.projects_api.create_approval_settings_rule(project_id, host, token, data)

    def migrate_mr_approvers(self, old_id, new_id, name):
        try:
            if self.are_enabled(old_id):
                self.log.info("Migrating merge request approvers for {}".format(name))
                self.migrate_merge_request_approvers(new_id, old_id)
                return True
            else:
                self.log.warning("Merge requests are disabled for project {}".format(name))
                return False
        except Exception, e:
            self.log.error("Failed to migrate {0} merge request approvers, with error:\n{1}".format(name, e))
            return False

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
                    created_rule_resp = self.projects_api.create_approval_settings_rule(
                        new_id, self.config.destination_host, self.config.destination_token, new_rule)

    def user_search_check_and_log(self, new_user, user, approver_ids):
        """
        :param new_user: A user entity from API search
        :param user: The user entity pulled from the list of approvers
        :param approver_ids: Current list of approver ids. Will be defaulted to an empty on None
        :return: The current approver_id list compose of approver_ids append the user id from the new_user, if found
        """
        if not approver_ids:
            approver_ids = []
        if not user:
            return approver_ids
        if new_user and isinstance(new_user, list):
            new_user_dict = new_user[0]
            if new_user_dict and isinstance(new_user_dict, dict):
                new_user_id = new_user_dict.get("id", None)
                if new_user_id:
                    approver_ids.append(new_user_id)
                else:
                    self.log.warn(
                        "Could not retrieve user id from {0}"
                            .format(new_user_dict)
                    )
            else:
                self.log.warn(
                    "Could not retrieve user dictionary from {0}"
                        .format(new_user[0])
                )
        else:
            self.log.warn(
                "Could not find merge request approver email {0} in destination system. {1}"
                    .format(user['email'], new_user)
            )

        return approver_ids

    def update_approvers(self, approval_data):
        approver_ids = []
        approver_groups = []
        for approved_user in approval_data["approvers"]:
            user = approved_user["user"]
            if user.get("id", None) is not None:
                user = self.users_api.get_user(
                    user["id"], self.config.source_host, self.config.source_token).json()
                new_user = api.search(
                    self.config.destination_host, self.config.destination_token, 'users', user['email'])
                approver_ids = self.user_search_check_and_log(new_user, user, approver_ids)
        for approved_group in approval_data["approver_groups"]:
            group = approved_group["group"]
            if group.get("id", None) is not None:
                group = self.groups_api.get_group(
                    group["id"], self.config.source_host, self.config.source_token).json()
                if self.config.parent_id is not None:
                    parent_group = self.groups_api.get_group(
                        self.config.parent_id, self.config.destination_host, self.config.destination_token).json()
                    group["full_path"] = "%s/%s" % (
                        parent_group["full_path"], group["full_path"])
                for new_group in self.groups_api.search_for_group(group["name"], self.config.destination_host, self.config.destination_token):
                    if new_group["full_path"].lower() == group["full_path"].lower():
                        approver_groups.append(new_group["id"])
                        break
        return approver_ids, approver_groups

    def update_approver_rule(self, rule):
        approver_ids = []
        approver_groups = []
        for user in rule["users"]:
            if user.get("id", None) is not None:
                user = self.users_api.get_user(
                    user["id"], self.config.source_host, self.config.source_token).json()
                new_user = api.search(
                    self.config.destination_host, self.config.destination_token, 'users', user['email'])
                approver_ids = self.user_search_check_and_log(new_user, user, approver_ids)
        for group in rule["groups"]:
            if group.get("id", None) is not None:
                group = self.groups_api.get_group(
                    group["id"], self.config.source_host, self.config.source_token).json()
                if self.config.parent_id is not None:
                    parent_group = self.groups_api.get_group(
                        self.config.parent_id, self.config.destination_host, self.config.destination_token).json()
                    group["full_path"] = "%s/%s" % (
                        parent_group["full_path"], group["full_path"])
                for new_group in self.groups_api.search_for_group(group["name"], self.config.destination_host, self.config.destination_token):
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
        self.projects_api.set_approval_configuration(
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
