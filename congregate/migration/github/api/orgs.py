from congregate.migration.github.api import base as api


class OrgsApi():
    def get_all_orgs(self, host):
        return api.list_all(host, "organizations")

    def get_org(self, host, key):
        return api.generate_get_request(host, "orgs/{}".format(key))

    def get_all_org_repos(self, host, key):
        return api.list_all(host, "orgs/{}/repos".format(key))

    def get_all_org_members(self, host, key):
        return api.list_all(host, "orgs/{}/members".format(key))
