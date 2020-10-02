import json
from congregate.helpers.base_class import BaseClass
from congregate.migration.bitbucket.api.groups import GroupsApi


class GroupsClient(BaseClass):
    GROUPS_TO_IGNORE = ["stash-users", "stash-local-all-users"]

    def __init__(self):
        self.groups_api = GroupsApi()
        super(GroupsClient, self).__init__()

    def retrieve_group_info(self):
        """
        List all BitBucket group metadata to be used for flat GitLab user mapping
        """
        groups = {}
        for group in self.groups_api.get_all_groups():
            group_name = group["name"].lower()
            if group_name not in self.GROUPS_TO_IGNORE:
                groups[group_name] = list(
                    self.groups_api.get_all_group_users(group["name"]))
        with open(f"{self.app_path}/data/bb_groups.json", "w") as f:
            json.dump(groups, f, indent=4)
        return groups
