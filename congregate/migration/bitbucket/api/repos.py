from congregate.migration.bitbucket.api import base as api

class ReposApi():

    def get_all_repos(self, host, token):
        return api.list_all(host, token, "repos")

