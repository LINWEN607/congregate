from congregate.migration.bitbucket_cloud.api.base import BitBucketCloudApi


class GroupsApi():
    def __init__(self):
        self.api = BitBucketCloudApi()

    def get_all_groups(self, workspace_slug):
        """
        Get a list of a groups for workspace. The caller must authenticate with administrative 
        rights on the workspace or as a group member to view a group.

        Core REST API: https://support.atlassian.com/bitbucket-cloud/docs/groups-endpoint/#GET-a-list-of-groups
        """
        return self.api.list_all(f"groups/{workspace_slug}")

    def get_all_group_users(self, workspace_slug, group):
        """
        Gets the membership for a group. The caller must authenticate with administrative rights on the account.

        Core REST API: https://support.atlassian.com/bitbucket-cloud/docs/groups-endpoint/#GET-the-group-members
        """
        return self.api.list_all(f"groups/{workspace_slug}/{group}/members")
