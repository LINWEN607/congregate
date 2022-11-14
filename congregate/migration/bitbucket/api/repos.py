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

    def get_all_repo_branches(self, project_key, repo_slug):
        """
        Retrieve the branches matching the supplied filterText param.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp211
        """
        return self.api.list_all(f"projects/{project_key}/repos/{repo_slug}/branches")

    def get_all_repo_pull_requests(self, project_key, repo_slug):
        """
        Retrieve a page of pull requests to or from the specified repository.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp292
        """
        return self.api.list_all(f"projects/{project_key}/repos/{repo_slug}/pull-requests?state=all")

    def get_all_repo_tags(self, project_key, repo_slug):
        """
        Retrieve the tags matching the supplied filterText param.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp396
        """
        return self.api.list_all(f"projects/{project_key}/repos/{repo_slug}/tags")

    def get_all_repo_commits(self, project_key, repo_slug):
        """
        Retrieve a page of commits from a given starting commit or "between" two commits.
        If no explicit commit is specified, the tip of the repository's default branch is assumed.
        commits may be identified by branch or tag name or by ID.
        A path may be supplied to restrict the returned commits to only those which affect that path.

        Core REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp223
        """
        return self.api.list_all(f"projects/{project_key}/repos/{repo_slug}/commits")

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

    def set_repo_user_permissions(self, project_key, repo_slug, data=None, message=None):
        """
        Promote or demote a user's permission level for the specified repository.

        Ref Restriction REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp286
        """
        return self.api.generate_put_request(f"projects/{project_key}/repos/{repo_slug}/permissions/users?{data}", data, description=message)

    def set_repo_group_permissions(self, project_key,  repo_slug, data=None, message=None):
        """
        Promote or demote a group's permission level for the specified repository.

        Ref Restriction REST API: https://docs.atlassian.com/bitbucket-server/rest/7.13.0/bitbucket-rest.html#idp280
        """
        return self.api.generate_put_request(f"projects/{project_key}/repos/{repo_slug}/permissions/groups?{data}", data, description=message)
