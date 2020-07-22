from congregate.migration.github.api.base import GitHubApi 


class UsersApi():
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.api = GitHubApi(self.host, self.token)
    def get_all_users(self):
        return self.api.list_all(self.host, "users")
    def get_user(self, slug):
        return self.api.__generate_v3_request_url(self.host, "users/{}".format(slug))

