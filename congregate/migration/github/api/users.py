from congregate.migration.github.api.base import base as api_users


class UsersApi():

    def get_all_users(self, host):
        return api_users.list_all(host, "users")
    def get_user(self, host, slug):
        return api_users.__generate_v3_request_url(host, "users/{}".format(slug))

