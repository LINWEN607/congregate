from congregate.migration.bitbucket.api import base as api

class UsersApi():

    def get_user(self, slug, host, token):
        return api.generate_get_request(host, token, "users/{}".format(slug))

    def get_all_users(self, host, token):
        return api.list_all(host, token, "admin/users")

