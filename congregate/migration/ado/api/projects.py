from congregate.migration.ado.api.base import AzureDevOpsApiWrapper


class ProjectsApi():
    def __init__(self):
        self.api = AzureDevOpsApiWrapper()

    def get_project(self, project_id):
        """
        Retrieve the project matching the supplied projectKey.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/core/projects/get?view=azure-devops-rest-7.1
        """
        return self.api.generate_get_request(f"_apis/projects/{project_id}")

    def get_all_projects(self):
        """
        Retrieve all projects.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/core/projects/list?view=azure-devops-rest-7.1&tabs=HTTP
        """
        return self.api.list_all("_apis/projects")

