from congregate.migration.bitbucket.api.base import BitBucketServerApi


class ProjectsApi():
    def __init__(self):
        self.api = BitBucketServerApi()

    def get_project(self, key):
        return self.api.generate_get_request(f"projects/{key}")

    def get_all_projects(self):
        return self.api.list_all("projects")

    def get_all_project_repos(self, key):
        return self.api.list_all(f"projects/{key}/repos")

    def get_all_project_users(self, key):
        return self.api.list_all(f"projects/{key}/permissions/users")

    def get_all_project_groups(self, key):
        return self.api.list_all(f"projects/{key}/permissions/groups")
