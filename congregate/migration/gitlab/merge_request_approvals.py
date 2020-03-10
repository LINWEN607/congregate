from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.migration.gitlab.version import VersionClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.users import UsersApi


class MergeRequestApprovalsClient(BaseClass):
    def __init__(self):
        self.version = VersionClient()
        self.users_api = UsersApi()
        self.groups_api = GroupsApi()
        self.projects_api = ProjectsApi()
        self.break_change_version = "11.10.0"
        super(MergeRequestApprovalsClient, self).__init__()

    def are_enabled(self, pid):
        project = self.projects_api.get_project(
            pid, self.config.source_host, self.config.source_token).json()
        return project.get("merge_requests_enabled", False)

    def migrate_project_level_mr_approvals(self, old_id, new_id, name):
        try:
            if self.are_enabled(old_id):
                self.log.info(
                    "Migrating merge request approvers for {}".format(name))
                self.migrate_project_approvals(new_id, old_id)
                return True
            else:
                self.log.warning(
                    "Merge requests are disabled for project {}".format(name))
                return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate {0} merge request approvers, with error:\n{1}".format(name, re))
            return False

    def migrate_project_approvals(self, new_id, old_id):
        # migrate configuration
        approval_data = self.projects_api.get_project_level_mr_approval_configuration(
            old_id, self.config.source_host, self.config.source_token).json()
        self.change_project_approval_configuration(new_id, approval_data)

        # migrate approval rules
        project_level_approval_rules = self.projects_api.get_all_project_level_mr_approval_rules(
            old_id, self.config.source_host, self.config.source_token)

        for rule in project_level_approval_rules:
            project_level_rule_params = self.get_project_level_rule_params(
                rule)
            self.projects_api.create_project_level_mr_approval_rule(
                new_id, self.config.destination_host, self.config.destination_token, project_level_rule_params)

    def migrate_mr_level_mr_approvals(self, old_id, new_id, name):
        pass

    def user_search_check_and_log(self, new_user, user, user_ids):
        """
        :param new_user: A user entity from API search
        :param user: The user entity pulled from the list of approvers
        :param user_ids: Current list of approver ids. Will be defaulted to an empty on None
        :return: The current user_id list compose of user_ids append the user id from the new_user, if found
        """
        if not user_ids:
            user_ids = []
        if not user:
            return user_ids
        if new_user and isinstance(new_user, list):
            new_user_dict = new_user[0]
            if new_user_dict and isinstance(new_user_dict, dict):
                new_user_id = new_user_dict.get("id", None)
                if new_user_id:
                    user_ids.append(new_user_id)
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
        return user_ids

    def get_rule_params(self, rule):
        user_ids = []
        group_ids = []
        protected_branch_ids = []
        for user in rule["users"]:
            if user.get("id", None) is not None:
                user = self.users_api.get_user(
                    user["id"], self.config.source_host, self.config.source_token).json()
                new_user = api.search(
                    self.config.destination_host, self.config.destination_token, 'users', user['email'])
                user_ids = self.user_search_check_and_log(
                    new_user, user, user_ids)
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
                        group_ids.append(new_group["id"])
                        break
        for p_branch in rule["protected_branches"]:
            pass
        return user_ids, group_ids, protected_branch_ids

    def change_project_approval_configuration(self, new_id, approval_data):
        approval_configuration = {
            "approvals_before_merge": approval_data["approvals_before_merge"],
            "reset_approvals_on_push": approval_data["reset_approvals_on_push"],
            "disable_overriding_approvers_per_merge_request": approval_data["disable_overriding_approvers_per_merge_request"],
            "merge_requests_author_approval": approval_data["merge_requests_author_approval"],
            "merge_requests_disable_committers_approval": approval_data["merge_requests_disable_committers_approval"],
            "require_password_to_approve": approval_data["require_password_to_approve"]
        }
        self.projects_api.change_project_level_mr_approval_configuration(
            new_id, self.config.destination_host, self.config.destination_token, approval_configuration)

    def get_project_level_rule_params(self, rule):
        for r in rule:
            user_ids, group_ids, protected_branch_ids = self.get_rule_params(r)
            yield {
                "name": rule["name"],
                "approvals_required": rule["approvals_required"],
                "user_ids": user_ids,
                "group_ids": group_ids,
                "protected_branch_ids": protected_branch_ids
            }
