from congregate.migration.bitbucket.api import base as api


class ReposApi():

    def get_all_repos(self, host):
        return api.list_all(host, "repos")

    def get_all_repo_users(self, host, project_key, repo_slug):
        return api.list_all(host, "projects/{0}/repos/{1}/permissions/users".format(project_key, repo_slug))
