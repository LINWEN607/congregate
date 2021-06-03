from congregate.migration.bitbucket.api.base import BitBucketServerApi


class ProjectsApi():
    def __init__(self):
        self.api = BitBucketServerApi()

    def get_project(self, key):
        """
        Retrieve the project matching the supplied projectKey.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp153
        """
        return self.api.generate_get_request(f"projects/{key}")

    def get_all_projects(self):
        """
        Retrieve all projects.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp149
        """
        return self.api.list_all("projects")

    def get_all_project_repos(self, key):
        """
        Retrieve all repositories from the project corresponding to the supplied projectKey.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp175
        """
        return self.api.list_all(f"projects/{key}/repos")

    def get_all_project_users(self, key):
        """
        Retrieve all users that have been granted at least one permission for the specified project.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp165
        """
        return self.api.list_all(f"projects/{key}/permissions/users")

    def get_all_project_groups(self, key):
        """
        Retrieve all groups that have been granted at least one permission for the specified project.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp159
        """
        return self.api.list_all(f"projects/{key}/permissions/groups")
