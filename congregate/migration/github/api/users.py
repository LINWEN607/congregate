from congregate.migration.github.api.base import GitHubApi


class UsersApi():
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.api = GitHubApi(self.host, self.token)

    def get_all_users(self):
        return self.api.list_all(self.host, "users", verify=False)

    def get_user(self, username):
        return self.api.generate_v3_get_request(self.host, "users/{}".format(username), verify=False)
