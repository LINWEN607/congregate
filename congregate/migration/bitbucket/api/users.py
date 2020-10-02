from congregate.migration.bitbucket.api.base import BitBucketServerApi


class UsersApi():
    def __init__(self):
        self.api = BitBucketServerApi()

    def get_user(self, slug):
        return self.api.generate_get_request(f"users/{slug}")

    def get_all_users(self):
        return self.api.list_all("admin/users")
