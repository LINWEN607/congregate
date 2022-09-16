from congregate.migration.bitbucket.api.base import BitBucketServerApi


class ReposApi():
    def __init__(self):
        self.api = BitBucketServerApi()

    def get_repo(self, project_key, repo_slug):
        """
        Retrieve the repository matching the supplied projectKey and repositorySlug.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp179
        """
        return self.api.generate_get_request(f"projects/{project_key}/repos/{repo_slug}")

    def get_all_repos(self):
        """
        Retrieve all repositories based on query parameters that control the search.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp442
        """
        return self.api.list_all("repos")

    def get_all_repo_users(self, project_key, repo_slug):
        """
        Retrieve all users that have been granted at least one permission for the specified repository.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp287
        """
        return self.api.list_all(f"projects/{project_key}/repos/{repo_slug}/permissions/users")

    def get_all_repo_groups(self, project_key, repo_slug):
        """
        Retrieve all groups that have been granted at least one permission for the specified repository.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp281
        """
        return self.api.list_all(f"projects/{project_key}/repos/{repo_slug}/permissions/groups")

    def get_repo_default_branch(self, project_key, repo_slug):
        """
        Retrieves the repository's default branch, if it has been created.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp287
        Deprecated as of 7.6 by GET /projects/{key}/repos/{slug}/default-branch
        """
        return self.api.generate_get_request(f"projects/{project_key}/repos/{repo_slug}/branches/default")

    def get_all_repo_branch_permissions(self, project_key, repo_slug):
        """
        Search for restrictions using the supplied parameters.

        Ref Restriction REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-ref-restriction-rest.html#idp4
        """
        return self.api.list_all(f"projects/{project_key}/repos/{repo_slug}/restrictions", branch_permissions=True)

    def create_repo_branch_permissions(self, project_key, repo_slug, data=None, message=None):
        """
        Create a restriction for the supplied branch or set of branches to be applied to the given repository.

        Ref Restriction REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-ref-restriction-rest.html#idp2
        """
        return self.api.generate_post_request(f"projects/{project_key}/repos/{repo_slug}/restrictions", data, branch_permissions=True, description=message)

    def delete_repo_branch_permission(self, project_key, repo_slug, rid, message=None):
        """
        Deletes a restriction as specified by a restriction id.

        Ref Restriction REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-ref-restriction-rest.html#idp7
        """
        return self.api.generate_delete_request(f"projects/{project_key}/repos/{repo_slug}/restrictions/{rid}", branch_permissions=True, description=message)
