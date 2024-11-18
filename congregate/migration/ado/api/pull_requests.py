from congregate.migration.ado.api.base import AzureDevOpsApiWrapper


class PullRequestsApi():
    def __init__(self):
        self.api = AzureDevOpsApiWrapper()

    def get_pull_request(self, project_id, repository_id, pull_request_id):
        """
        Retrieve the pull request matching the supplied project_id and repository_id and pull_request_id

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-requests/get-pull-request?view=azure-devops-rest-7.1
        """
        return self.api.generate_get_request(f"{project_id}/_apis/git/repositories/{repository_id}/pullrequests/{pull_request_id}")

    def get_all_pull_requests(self, project_id, repository_id):
        """
        Retrieve all pull requests.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-requests/get-pull-requests?view=azure-devops-rest-7.1&tabs=HTTP
        """
        params = {
            "status": "all"
        }
        return self.api.list_all(f"{project_id}/_apis/git/repositories/{repository_id}/pullrequests", params=params)
