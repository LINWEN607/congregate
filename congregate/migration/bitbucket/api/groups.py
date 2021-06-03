from congregate.migration.bitbucket.api.base import BitBucketServerApi


class GroupsApi():
    def __init__(self):
        self.api = BitBucketServerApi()

    def get_all_groups(self):
        """
        Retrieve all groups.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp5
        """
        return self.api.list_all("admin/groups")

    def get_all_group_users(self, group):
        """
        Retrieves all users that are members of a specified group.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp11
        """
        return self.api.list_all(f"admin/groups/more-members?context={group}")
