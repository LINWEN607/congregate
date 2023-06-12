from requests.exceptions import RequestException
from dacite import from_dict

from congregate.helpers.db_or_http import DbOrHttpMixin
from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.meta.api_models.mr_level_approvers import MergeRequestLevelApproverPayload
from congregate.migration.meta.api_models.project_level_approvers import ProjectLevelApproverPayload


class MergeRequestApprovalsClient(DbOrHttpMixin, BaseGitLabClient):
    def __init__(self, src_host=None, src_token=None, dest_host=None, dest_token=None):
        self.users_api = UsersApi()
        self.groups_api = GroupsApi()
        self.groups = GroupsClient()
        self.projects_api = ProjectsApi()
        super(MergeRequestApprovalsClient, self).__init__(src_host=src_host, src_token=src_token, dest_host=dest_host, dest_token=dest_token)

    def are_enabled(self, pid):
        project = self.projects_api.get_project(
            pid, self.config.source_host, self.config.source_token).json()
        return project.get("merge_requests_enabled", False)

    def migrate_project_level_mr_approvals(self, old_id, new_id, name):
        try:
            if self.are_enabled(old_id):
                return self.migrate_project_approvals(new_id, old_id, name)
            else:
                self.log.warning(
                    "Merge requests are disabled for project {}".format(name))
        except Exception as e:
            self.log.error(
                "Failed to migrate project-level MR approvals for {0}, with error:\n{1}".format(name, e))
            return False

    def migrate_project_approvals(self, new_id, old_id, name):
        try:
            # migrate configuration
            conf = safe_json_response(self.projects_api.get_project_level_mr_approval_configuration(
                old_id, self.src_host, self.src_token))
            error, conf = is_error_message_present(conf)
            if error or not conf:
                self.log.error(
                    "Failed to fetch MR approval configuration ({0}) for project {1}".format(conf, name))
                return False
            self.log.info(
                "Migrating project-level MR approval configuration for {0} (ID: {1})".format(name, old_id))
            conf = from_dict(data_class=ProjectLevelApproverPayload(), data=conf)
            self.projects_api.change_project_level_mr_approval_configuration(
                new_id, self.dest_host, self.dest_token, conf)

            # migrate approval rules
            resp = self.get_data(
                    self.projects_api.get_all_project_level_mr_approval_rules,
                    (old_id, self.src_host, self.src_token),
                    'mr_approvers',
                    old_id,
                    airgap=self.config.airgap,
                    airgap_import=self.config.airgap_import)
            approval_rules = iter(resp)
            self.log.info(
                "Migrating project-level MR approval rules for {0} (ID: {1})".format(name, old_id))
            for rule in approval_rules:
                error, rule = is_error_message_present(rule)
                if error or not rule:
                    self.log.error(
                        "Failed to fetch MR approval rules ({0}) for project {1}".format(rule, name))
                    return False
                user_ids, group_ids, protected_branch_ids = self.get_missing_rule_params(
                    rule, new_id)
                data = MergeRequestLevelApproverPayload(
                    name=rule['name'],
                    approvals_required=rule["approvals_required"],
                    user_ids=user_ids,
                    group_ids=group_ids,
                    protected_branch_ids=protected_branch_ids
                )
                self.send_data(
                    self.projects_api.create_project_level_mr_approval_rule,
                    (new_id, self.dest_host, self.dest_token),
                    'mr_approvers', 
                    new_id, 
                    data.to_dict(),
                    airgap=self.config.airgap,
                    airgap_export=self.config.airgap_export
                )
            return True
        except TypeError as te:
            self.log.error(
                "Project {0} MR approvals {1} {2}".format(name, resp, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate project-level MR approvals for {0}, with error:\n{1}".format(name, re))
            return False

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
                    self.log.warning(
                        "Could not retrieve user id from {0}".format(new_user_dict))
            else:
                self.log.warning(
                    "Could not retrieve user dictionary from {0}".format(new_user[0]))
        else:
            self.log.warning("Could not find merge request approver email {0} in destination system. {1}".format(
                user['email'], new_user))
        return user_ids

    def get_missing_rule_params(self, rule, pid):
        user_ids = []
        group_ids = []
        p_branch_ids = []
        for u in rule["users"]:
            if u.get("id", None):
                if user := safe_json_response(self.users_api.get_user(
                        u["id"], self.config.source_host, self.config.source_token)):
                    new_user = self.users_api.api.search(
                        self.config.destination_host, self.config.destination_token, "users", user["email"])
                    user_ids = self.user_search_check_and_log(
                        new_user, user, user_ids)
        for g in rule["groups"]:
            if g.get("id", None):
                if group := safe_json_response(self.groups_api.get_group(
                        g["id"], self.config.source_host, self.config.source_token)):
                    if self.config.dstn_parent_id:
                        group["full_path"] = f"{self.config.dstn_parent_group_path}/{group['full_path']}"
                    dst_gid = self.groups.find_group_id_by_path(
                        self.config.destination_host, self.config.destination_token, group["full_path"])
                    if dst_gid:
                        group_ids.append(dst_gid)
                        break
        for pb in rule["protected_branches"]:
            if pb.get("name", None):
                p_branch = safe_json_response(self.projects_api.get_single_project_protected_branch(
                    pid, pb["name"], self.config.destination_host, self.config.destination_token))
                if p_branch and p_branch.get("id", None):
                    p_branch_ids.append(p_branch["id"])
        return user_ids, group_ids, p_branch_ids
