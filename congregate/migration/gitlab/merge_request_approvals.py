from httpx import RequestError
from dacite import from_dict

from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response

from congregate.helpers.migrate_utils import search_for_user_by_user_mapping_field
from congregate.helpers.db_or_http import DbOrHttpMixin
from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
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
        super().__init__(src_host=src_host, src_token=src_token,
                         dest_host=dest_host, dest_token=dest_token)

    def are_enabled(self, pid):
        project = self.projects_api.get_project(
            pid, self.config.source_host, self.config.source_token).json()
        return project.get("merge_requests_enabled", False)

    def migrate_project_level_mr_approvals(self, old_id, new_id, name):
        try:
            if self.config.airgap and self.config.airgap_import:
                return self.migrate_project_approvals(new_id, old_id, name)
            if self.are_enabled(old_id):
                return self.migrate_project_approvals(new_id, old_id, name)
            self.log.warning(
                f"Merge requests are disabled for project '{name}'")
            return None
        except Exception as e:
            self.log.error(
                f"Failed to migrate project '{name}' MR approvals:\n{e}")
            return False

    def migrate_project_approvals(self, new_id, old_id, name):
        try:
            if not self.config.airgap:
                # migrate configuration
                conf = safe_json_response(self.projects_api.get_project_level_mr_approval_configuration(
                    old_id, self.src_host, self.src_token))
                error, conf = is_error_message_present(conf)
                if error or not conf:
                    self.log.error(
                        f"Failed to fetch project '{name}' MR approval configuration ({conf})")
                    return False
                self.log.info(
                    f"Migrating project '{name}' MR approval configuration")
                conf_payload = from_dict(
                    data_class=ProjectLevelApproverPayload, data=conf)
                self.projects_api.change_project_level_mr_approval_configuration(
                    new_id, self.dest_host, self.dest_token, conf_payload.to_dict())

            # migrate approval rules
            resp = self.get_data(
                self.projects_api.get_all_project_level_mr_approval_rules,
                (old_id, self.src_host, self.src_token),
                'mr_approvers',
                old_id,
                airgap=self.config.airgap,
                airgap_import=self.config.airgap_import)
            approval_rules = iter(resp)
            self.log.info(f"Migrating project '{name}' MR approval rules")
            for rule in approval_rules:
                error, rule = is_error_message_present(rule)
                if error or not rule:
                    self.log.error(
                        f"Failed to fetch project '{name}' MR approval rules ({rule})")
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
            self.log.error(f"Project '{name}' MR approvals:\n{te}")
            return False
        except RequestError as re:
            self.log.error(
                f"Failed to migrate project '{name}' MR approvals:\n{re}")
            return False

    def user_search_check_and_log(self, new_user, user, user_ids, field):
        """
        :param new_user: A user entity from API search
        :param user: The user entity pulled from the list of approvers
        :param user_ids: Current list of approver ids. Will be defaulted to an empty on None
        :return: The current user_id list compose of user_ids append the user id from the new_user, if found
        """
        if new_user and isinstance(new_user, dict):
            if new_user_id := new_user.get("id"):
                user_ids.append(new_user_id)
                return user_ids
        self.log.warning(
            f"Could not find MR approver {field} '{user[field]}' on destination:\n{new_user}")
        return user_ids

    def get_missing_rule_params(self, rule, pid):
        user_ids = []
        group_ids = []
        p_branch_ids = []
        s_host = self.config.source_host
        s_token = self.config.source_token
        d_host = self.config.destination_host
        d_token = self.config.destination_token
        for u in rule["users"]:
            if u.get("id"):
                if user := safe_json_response(self.users_api.get_user(u["id"], s_host, s_token)):
                    field = self.config.user_mapping_field
                    new_user = search_for_user_by_user_mapping_field(
                            field, user, d_host, d_token)
                    user_ids = self.user_search_check_and_log(
                        new_user, user, user_ids, field)
        for g in rule["groups"]:
            if g.get("id"):
                if group := safe_json_response(self.groups_api.get_group(g["id"], s_host, s_token)):
                    full_path = group["full_path"]
                    if self.config.dstn_parent_id:
                        full_path = f"{self.config.dstn_parent_group_path}/{full_path}"
                    dst_gid = self.groups.find_group_id_by_path(
                        d_host, d_token, full_path)
                    if dst_gid:
                        self.log.info(f"Found project MR approval rule '{rule.get('name')}' group {dst_gid} on destination")
                        group_ids.append(dst_gid)
        for pb in rule["protected_branches"]:
            if pb.get("name"):
                p_branch = safe_json_response(self.projects_api.get_single_project_protected_branch(
                    pid, pb["name"], d_host, d_token))
                if p_branch and p_branch.get("id"):
                    p_branch_ids.append(p_branch["id"])
        return user_ids, group_ids, p_branch_ids
