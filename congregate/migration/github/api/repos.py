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

    def get_repo_pulls(self, owner, repo, state="all"):
        """
        List repository pull requests.
        Default behavior returns all pull requests.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/pulls#list-pull-requests
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/pulls?state={state}")

    def get_repo_tags(self, owner, repo):
        """
        List repository tags.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-repository-tags
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/tags")

    def get_repo_milestones(self, owner, repo, state="all"):
        """
        List repository milestones.
        Default behavior returns all milestones.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/issues#list-milestones
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/milestones?state={state}")

    def get_repo_issues(self, owner, repo, state="all"):
        """
        List repository issues.
        Default behavior returns all milestones.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/issues#list-repository-issues
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/issues?state={state}")

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
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/teams")

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
        yield self.api.list_all(self.host, f"users/{username}/repos")

    def get_all_repo_collaborators(self, owner, repo):
        """
        List repository collaborators.
        Requires a collaborator PAT.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repository-collaborators
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/collaborators")

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

    def get_single_project_protected_branch(self, owner, repo, branch):
        """
        Gets branch protection.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#get-branch-protection
        """
        return self.api.generate_v3_get_request(self.host, f"repos/{owner}/{repo}/branches/{branch}/protection")
