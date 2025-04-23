from congregate.migration.bitbucket_cloud.api.base import BitBucketCloudApi


class UsersApi():
    def __init__(self):
        self.api = BitBucketCloudApi()

    def get_user(self, userID):
        """
        Retrieve the user matching the supplied userID.
        :param userID: (str) This can either be an Atlassian Account ID OR the UUID of the account, surrounded by curly-braces, for example: {account UUID}.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-users/#api-users-selected-user-get
        """
        return self.api.generate_get_request(f"users/{userID}")

    def get_all_users(self, workspace_slug):
        """
        Returns all members of the requested workspace.

        This endpoint additionally supports filtering by email address, if called by a workspace administrator, integration or workspace access token. 
        This is done by adding the following query string parameter: q=user.email IN ("user1@org.com","user2@org.com")

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-workspaces/#api-workspaces-workspace-members-get
        """
        return self.api.list_all(f"workspaces/{workspace_slug}/members")
    
    def get_user_ssh_keys(self, userID):
        """
        Returns a paginated list of the user's SSH public keys.

        :param userID: (str) This can either be an Atlassian Account ID OR the UUID of the account, surrounded by curly-braces, for example: {account UUID}.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-ssh/#api-users-selected-user-ssh-keys-get
        """
        return self.api.generate_get_request(f"users/{userID}/ssh-keys")


