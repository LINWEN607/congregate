from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
import requests


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

    def get_all_pull_requests_in_tfs(self, project_id, repository_id):
        """
        Retrieve all pull requests.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-requests/get-pull-requests?view=azure-devops-rest-7.1&tabs=HTTP
        """
        params = {
            "status": "all",
            "$top": 50
        }
        return self.api.list_all_in_tfs(f"{project_id}/_apis/git/repositories/{repository_id}/pullrequests", params=params)


    def get_all_pull_request_threads(self, project_id, repository_id, pull_request_id):
        """
        Retrieve all threads for a pull request.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-request-threads/list?view=azure-devops-rest-7.1
        """
        return self.api.list_all(f"{project_id}/_apis/git/repositories/{repository_id}/pullrequests/{pull_request_id}/threads")
    
    def get_all_pull_request_thread_comments(self, project_id, repository_id, pull_request_id, thread_id):
        """
        Retrieve all comments for a thread.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/comments/list?view=azure-devops-rest-7.1
        """
        return self.api.list_all(f"{project_id}/_apis/git/repositories/{repository_id}/pullrequests/{pull_request_id}/threads/{thread_id}/comments")
    
    def get_all_pull_request_commits(self, project_id, repository_id, pull_request_id):
        """
        Retrieve all commits for a pull request.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-request-commits/get-pull-request-commits?view=azure-devops-rest-7.1
        """
        return self.api.list_all(f"{project_id}/_apis/git/repositories/{repository_id}/pullrequests/{pull_request_id}/commits")
    
    def get_pull_request_diffs(self, project_id, repository_id, source_sha, target_sha):
        """
        Retrieve all diffs for a pull request.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-request-commits/get-pull-request-commits?view=azure-devops-rest-7.1
        """
        return self.api.generate_get_request(f"{project_id}/_apis/git/repositories/{repository_id}/diffs/commits?baseVersion={source_sha}&baseVersionType=commit&targetVersion={target_sha}&targetVersionType=commit&api-version=7.1")

    def download_file_from_ado(self, object_url, token):
        """
        Downloads the file from the given ADO file URL using the ADO source token for authentication.
        NOTE: This is a quick implementation that can be refined later to follow the same pattern from the api class

        :param object_url: The URL of the file hosted on the ADO server.
        :return: Response with the content of the file if successful, or None if the download fails.
        """

        headers = {
            "Authorization": f"Basic {token}"
        }
        return requests.get(object_url, headers=headers, stream=True, timeout=15)

    def get_all_pull_request_reviewers(self, project_id, repository_id, pull_request_id):
        """
        Retrieve all reviewers for a pull request.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-request-reviewers/get-pull-request-reviewers?view=azure-devops-rest-7.1
        """
        return self.api.list_all(f"{project_id}/_apis/git/repositories/{repository_id}/pullrequests/{pull_request_id}/reviewers")
