from congregate.migration.ado.api.base import AzureDevOpsApiWrapper

class RepositoriesApi():
    def __init__(self):
        self.api = AzureDevOpsApiWrapper()

    def get_repository(self, repository_id):
        """
        Retrieve the project matching the supplied projectKey.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/repositories/get-repository?view=azure-devops-rest-7.0&tabs=HTTP
        """
        return self.api.generate_get_request(f"_apis/git/repositories/{repository_id}")

    def get_all_repositories(self, project_id):
        """
        Retrieve all repos.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/repositories/list?view=azure-devops-rest-7.0&tabs=HTTP
        """
        return self.api.list_all(f"{project_id}/_apis/git/repositories")