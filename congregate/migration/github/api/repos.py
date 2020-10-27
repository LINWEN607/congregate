import json

from congregate.migration.github.api.base import GitHubApi
from congregate.helpers.conf import Config


class ReposApi():
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.api = GitHubApi(self.host, self.token)
        self.config = Config()

    def get_repo(self, owner, repo):
        """
        Get a repository

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#get-a-repository
        """
        return self.api.generate_v3_get_request(
            self.host,
            f"repos/{owner}/{repo}"
        )

    def get_repo_commits(self, owner, repo):
        """
        List repository commits.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-commits
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/commits")

    def get_repo_branches(self, owner, repo):
        """
        List repository branches.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-branches
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/branches")

    def get_repo_pulls(self, owner, repo):
        """
        List repository pull requests.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/pulls#list-pull-requests
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/pulls")

    def get_repo_tags(self, owner, repo):
        """
        List repository tags.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-repository-tags
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/tags")

    def get_repo_milestones(self, owner, repo):
        """
        List repository milestones.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/issues#list-milestones
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/milestones")

    def get_repo_releases(self, owner, repo):
        """
        List repository releases.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-releases
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/releases")

    def get_repo_pr_comments(self, owner, repo, issue):
        """
        List pull request comments.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/issues#list-issue-comments
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/issues/{issue}/comments")

    def get_repo_teams(self, owner, repo):
        """
        List repository teams.
        Available only for org repos, otherwise returns 404.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repository-teams
        """
        return self.api.list_all(self.host, "repos/{}/{}/teams".format(owner, repo))

    def get_all_public_repos(self, page_check=False):
        """
        Lists all public repositories in the order that they were created.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-public-repositories
        """
        return self.api.list_all(self.host, "repositories", page_check=page_check)

    def get_all_user_repos(self, username):
        """
        Lists public repositories for the specified user.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repositories-for-a-user
        """
        yield self.api.list_all(self.host, "users/{}/repos".format(username))

    def get_all_repo_collaborators(self, owner, repo):
        """
        List repository collaborators.
        Requires a collaborator PAT.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repository-collaborators
        """
        return self.api.list_all(self.host, "repos/{}/{}/collaborators".format(owner, repo))

    def create_auth_user_repo(self, data=None, message=None):
        """
        Creates a new repository for the authenticated user.

        GitHub API v3 Doc: https://docs.github.com/en/enterprise/2.21/user/rest/reference/repos#create-a-repository-for-the-authenticated-user
        """
        if not message:
            print(
                f"Creating a new repository for the authenticated user {data}")

        return self.api.generate_v3_post_request(
            self.host,
            "user/repos",
            json.dumps(data),
            description=message
        )

    def create_org_repo(self, org_name, data=None, message=None):
        """
        Create an organization repository.

        GitHub API v3 Doc: https://docs.github.com/en/enterprise/2.21/user/rest/reference/repos#create-an-organization-repository
        """
        if not message:
            print(f"Creating an organization repository {data}")

        return self.api.generate_v3_post_request(
            self.host,
            f"orgs/{org_name}/repos",
            data,
            description=message
        )
