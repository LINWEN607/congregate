from congregate.migration.bitbucket.api import base as api


class ProjectsApi():

    def get_project(self, key, host, token):
        return api.generate_get_request(host, token, "projects/{}".format(key))

    def get_all_projects(self, host, token):
        return api.list_all(host, token, "projects")

    def get_all_project_repos(self, key, host, token):
        return api.list_all(host, token, "projects/{}/repos".format(key))

    def get_all_project_users(self, key, host, token):
        return api.list_all(host, token, "projects/{}/permissions/users".format(key))
