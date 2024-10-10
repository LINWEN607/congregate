from congregate.migration.ado.api.base import AzureDevOpsApiWrapper


class UsersApi():
    def __init__(self):
        self.api = AzureDevOpsApiWrapper()

    def get_user(self, descriptor):
        """
        Retrieve the user matching the supplied userDescriptor.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/graph/users/get?view=azure-devops-rest-7.1&tabs=HTTP
        """
        return self.api.generate_request_url(f"/_apis/graph/users/{descriptor}", sub_api="vssps")

    def get_all_users(self):
        """
        Retrieve all users.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/graph/users/list?view=azure-devops-rest-7.1&tabs=HTTP
        """
        return self.api.list_all("_apis/graph/users", sub_api="vssps")
