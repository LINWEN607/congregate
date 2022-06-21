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

    def get_all_project_branch_permissions(self, project_key):
        """
        Search for restrictions using the supplied parameters.

        Ref Restriction REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-ref-restriction-rest.html#idp11
        """
        return self.api.list_all(f"projects/{project_key}/restrictions", branch_permissions=True)

    def create_project_branch_permissions(self, project_key, data=None, message=None):
        """
        Create a restriction for the supplied branch or set of branches to be applied on all repositories in the given project.

        Ref Restriction REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-ref-restriction-rest.html#idp9
        """
        return self.api.generate_post_request(f"projects/{project_key}/restrictions", data, branch_permissions=True, description=message)

    def delete_project_branch_permission(self, project_key, rid, message=None):
        """
        Deletes a restriction as specified by a restriction id.

        Ref Restriction REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-ref-restriction-rest.html#idp14
        """
        return self.api.generate_delete_request(f"projects/{project_key}/restrictions/{rid}", branch_permissions=True, description=message)
