from congregate.migration.github.api.base import GitHubApi
from congregate.helpers.conf import Config

class UsersApi():
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.api = GitHubApi(self.host, self.token)
        self.config = Config()

    def get_all_users(self):
        """
        Lists all users, in the order that they signed up on GitHub. This list includes personal user accounts and organization accounts.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/users#list-users
        """
        return self.api.list_all(self.host, "users")

    def get_user(self, username):
        """
        Provides publicly available information about someone with a GitHub account.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/users#get-a-user
        """
        return self.api.generate_v3_get_request(self.host, f"users/{username}")

    def get_import_user(self):
        return self.api.generate_v3_get_request(self.host, "user")
