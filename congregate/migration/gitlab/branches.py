from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi
import json


class BranchesClient(BaseClass):
    def __init__(self):
        self.users = UsersApi()
        self.groups = GroupsApi()
        super(BranchesClient, self).__init__()

    def get_branches(self, id, host, token):
        return api.list_all(host, token, "projects/%d/repository/branches" % id)

    def get_protected_branches(self, id, host, token):
        return api.list_all(host, token, "projects/%d/protected_branches" % id)

    def protect_branch(self, id, host, token, branch_name, push_access_level=None, merge_access_level=None, allowed_to_push=None, allowed_to_merge=None, allowed_to_unprotect=None):
        data = {
            "name": branch_name
        }
        if push_access_level is not None:
            data["push_access_level"] = push_access_level
        if merge_access_level is not None:
            data["merge_access_level"] = merge_access_level
        if allowed_to_push is not None:
            data["allowed_to_push"] = allowed_to_push
        if allowed_to_merge is not None:
            data["allowed_to_merge"] = allowed_to_merge
        if allowed_to_unprotect is not None:
            data["allowed_to_unprotect"] = allowed_to_unprotect
        return api.generate_post_request(host, token, "projects/%d/protected_branches" % id, json.dumps(data))

    def update_access_levels(self, access_level):
        for a in access_level:
            if a.get("user_id", None) is not None:
                user = self.users.get_user(
                    a["user_id"], self.config.source_host, self.config.source_token).json()
                new_user = api.search(
                    self.config.destination_host, self.config.destination_token, 'users', user['email'])
                new_user_id = new_user[0]["id"]
                a["user_id"] = new_user_id
            if a.get("group_id", None) is not None:
                group = self.groups.get_group(
                    a["group_id"], self.config.source_host, self.config.source_token).json()
                if self.config.parent_id is not None:
                    parent_group = self.groups.get_group(
                        self.config.parent_id, self.config.destination_host, self.config.destination_token).json()
                    group["full_path"] = "%s/%s" % (
                        parent_group["full_path"], group["full_path"])
                for new_group in self.groups.search_for_group(group["name"], self.config.destination_host, self.config.destination_token):
                    if new_group["full_path"].lower() == group["full_path"].lower():
                        a["group_id"] = new_group["id"]
                        break

        return access_level

    def migrate_protected_branches(self, id, old_id):
        for branch in self.get_protected_branches(old_id, self.config.source_host, self.config.source_token):
            allowed_to_push = self.update_access_levels(
                branch["push_access_levels"])
            allowed_to_merge = self.update_access_levels(
                branch["merge_access_levels"])
            allowed_to_unprotect = self.update_access_levels(
                branch["unprotect_access_levels"])

            self.protect_branch(id, self.config.destination_host, self.config.destination_token,
                                branch["name"], allowed_to_push=allowed_to_push, allowed_to_merge=allowed_to_merge, allowed_to_unprotect=allowed_to_unprotect)
