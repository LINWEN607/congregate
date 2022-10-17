from gitlab_ps_utils.json_utils import write_json_to_file

from congregate.migration.bitbucket.api.groups import GroupsApi
from congregate.migration.bitbucket.base import BitBucketServer


class GroupsClient(BitBucketServer):
    GROUPS_TO_IGNORE = ["stash-users", "stash-local-all-users"]

    def __init__(self):
        self.groups_api = GroupsApi()
        super().__init__()

    def retrieve_group_info(self):
        """
        List all BitBucket group metadata to be used for flat GitLab user mapping
        """
        groups = {}
        for group in self.groups_api.get_all_groups():
            group_name = group["name"].lower()
            if group_name not in self.GROUPS_TO_IGNORE:
                groups[group_name] = {}
                groups[group_name]["users"] = self.get_users_list(
                    group["name"])
                groups[group_name]["repos"] = []
                groups[group_name]["projects"] = []
        write_json_to_file(
            f"{self.app_path}/data/bb_groups.json", groups, self.log)
        return groups

    def get_users_list(self, group_name):
        users_list = [self.format_user(
            u) for u in self.groups_api.get_all_group_users(group_name)]
        # Remove None values
        return [u for u in users_list if u]
