from congregate.migration.bitbucket.api.base import BitBucketServerApi


class GroupsApi():
    def __init__(self):
        self.api = BitBucketServerApi()

    def get_all_groups(self):
        return self.api.list_all("admin/groups")

    def get_all_group_users(self, group):
        return self.api.list_all(f"admin/groups/more-members?context={group}")
