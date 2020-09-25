from congregate.migration.github.api.base import GitHubApi
from congregate.helpers.conf import Config

class TeamsApi():
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.api = GitHubApi(self.host, self.token)
        self.config = Config()

    def get_team_repos(self, team_id):
        """
        List repository teams.
        Available only for org repos, otherwise returns 404.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repository-teams
        """
        return self.api.list_all(self.host, f"team/{team_id}/repos")
