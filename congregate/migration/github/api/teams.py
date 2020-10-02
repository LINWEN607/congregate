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
        List team repositories.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repository-teams
        """
        return self.api.list_all(self.host, f"teams/{team_id}/repos")

    def get_team_members(self, team_id):
        """
        List team members.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/teams#list-team-members-legacy
        """
        return self.api.list_all(self.host, f"teams/{team_id}/members")