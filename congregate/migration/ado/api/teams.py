from congregate.migration.ado.api.base import AzureDevOpsApiWrapper


class TeamsApi():
    def __init__(self):
        self.api = AzureDevOpsApiWrapper()

    def get_teams(self, project_id):
        """
        Get a list of teams.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/core/teams/get-teams?view=azure-devops-rest-7.0&tabs=HTTP
        """
        return self.api.generate_get_request(f"_apis/projects/{project_id}/teams")

    def get_team(self, project_id, team_id):
        """
        Get a specific team.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/core/teams/get?view=azure-devops-rest-7.0&tabs=HTTP
        """
        return self.api.generate_get_request(f"_apis/projects/{project_id}/teams/{team_id}")

    def get_team_members(self, project_id, team_id):
        """
       Get a list of members for a specific team.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/core/teams/get-team-members-with-extended-properties?view=azure-devops-rest-7.0&tabs=HTTP
         """
        return self.api.generate_get_request(f"_apis/projects/{project_id}/teams/{team_id}/members")
