from congregate.migration.bitbucket.api.base import BitBucketServerApi


class UsersApi():
    def __init__(self):
        self.api = BitBucketServerApi()

    def get_user(self, slug):
        """
        Retrieve the user matching the supplied userSlug.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp456
        """
        return self.api.generate_get_request(f"users/{slug}")

    def get_all_users(self):
        """
        Retrieve all users.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp17
        """
        return self.api.list_all("admin/users")

    def get_user_permissions(self, slug):
        """
        Retrieve a page of users that have been granted at least one global permission.
        The authenticated user must have ADMIN permission or higher to call this resource.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp69
        """
        return self.api.list_all(f"admin/permissions/users?filter={slug}")
