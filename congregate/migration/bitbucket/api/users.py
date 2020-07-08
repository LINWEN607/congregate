from congregate.migration.bitbucket.api import base as api


class UsersApi():

    def get_user(self, slug, host):
        return api.generate_get_request(host, "users/{}".format(slug))

    def get_all_users(self, host):
        return api.list_all(host, "admin/users")
