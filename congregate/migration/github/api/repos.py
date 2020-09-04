from congregate.migration.github.api.base import GitHubApi
import json
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
        return self.api.generate_v3_get_request(self.host, "repos/{}/{}".format(owner, repo))

    def get_repo_teams(self, owner, repo):
        """
        List repository teams.
        Available only for org repos, otherwise returns 404.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repository-teams
        """
        return self.api.list_all(self.host, "repos/{}/{}/teams".format(owner, repo))

    def get_all_public_repos(self):
        """
        Lists all public repositories in the order that they were created.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-public-repositories
        """
        return self.api.list_all(self.host, "repositories")

    def get_all_user_repos(self, username):
        """
        Lists public repositories for the specified user.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repositories-for-a-user
        """
        return self.api.list_all(self.host, "users/{}/repos".format(username))

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
            print(f"Creating a new repository for the authenticated user {data}")

        return self.api.generate_v3_post_request(self.host, "user/repos", json.dumps(data), description=message)
