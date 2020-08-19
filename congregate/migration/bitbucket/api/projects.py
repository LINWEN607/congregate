from congregate.migration.bitbucket.api import base as api


class ProjectsApi():
    def get_project(self, key, host):
        return api.generate_get_request(host, "projects/{}".format(key))

    def get_all_projects(self, host):
        return api.list_all(host, "projects")

    def get_all_project_repos(self, key, host):
        return api.list_all(host, "projects/{}/repos".format(key))

    def get_all_project_users(self, key, host):
        return api.list_all(host, "projects/{}/permissions/users".format(key))

    def get_all_project_groups(self, key, host):
        return api.list_all(host, "projects/{}/permissions/groups".format(key))
