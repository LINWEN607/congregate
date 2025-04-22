from congregate.migration.bitbucket_cloud.api.base import BitBucketCloudApi

class ReposApi():
    def __init__(self):
        self.api = BitBucketCloudApi()

    def get_workspaces(self):
        """
        Get all workspaces accessible to the authenticated user
        """
        return self.api.list_all("workspaces")

    def get_repo(self, workspace_slug, repo_slug):
        """
        Retrieve the repository matching the supplied projectKey and repositorySlug.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/#api-repositories-workspace-repo-slug-get
        """
        return self.api.generate_get_request(f"repositories/{workspace_slug}/{repo_slug}")

    def get_all_repos(self, workspace_slug):
        """
        Retrieve all repositories based on query parameters that control the search.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/#api-repositories-workspace-get
        """
        return self.api.list_all(f"repositories/{workspace_slug}")

    def get_all_repo_users(self, workspace_slug, repo_slug):
        """
        Retrieve all users that have been granted at least one permission for the specified repository.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/#api-repositories-workspace-repo-slug-permissions-config-users-get
        """
        return self.api.list_all(f"repositories/{workspace_slug}/{repo_slug}/permissions-config/users")

    def get_all_repo_groups(self, workspace_slug, repo_slug):
        """
        Retrieve all groups that have been granted at least one permission for the specified repository.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/#api-repositories-workspace-repo-slug-permissions-config-groups-get
        """
        return self.api.list_all(f"repositories/{workspace_slug}/{repo_slug}/permissions-config/groups")

    def get_all_repo_branches(self, workspace_slug, repo_slug):
        """
        Retrieve the branches matching the supplied filterText param.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-refs/#api-repositories-workspace-repo-slug-refs-get
        """
        return self.api.list_all(f"repositories/{workspace_slug}/{repo_slug}/refs")

    def get_all_repo_pull_requests(self, workspace_slug, repo_slug):
        """
        Retrieve a page of pull requests to or from the specified repository.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pullrequests/#api-repositories-workspace-repo-slug-pullrequests-get
        """
        return self.api.list_all(f"repositories/{workspace_slug}/{repo_slug}/pullrequests")

    def get_all_repo_tags(self, workspace_slug, repo_slug):
        """
        Retrieve the tags matching the supplied filterText param.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-refs/#api-repositories-workspace-repo-slug-refs-get
        """
        return self.api.list_all(f"repositories/{workspace_slug}/{repo_slug}/refs")

    def get_all_repo_commits(self, workspace_slug, repo_slug):
        """
        Retrieve a page of commits from a given starting commit or "between" two commits.
        If no explicit commit is specified, the tip of the repository's default branch is assumed.
        commits may be identified by branch or tag name or by ID.
        A path may be supplied to restrict the returned commits to only those which affect that path.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-commits/#api-repositories-workspace-repo-slug-commits-get
        """
        return self.api.list_all(f"repositories/{workspace_slug}/{repo_slug}/commits")