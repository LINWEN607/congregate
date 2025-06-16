from congregate.migration.ado.api.base import AzureDevOpsApiWrapper


class WorkItemsApi():
    def __init__(self):
        self.api = AzureDevOpsApiWrapper()

    def get_work_item(self, project_id, work_item_id):
        """
        Retrieve the work item matching the supplied project_id and work_item_id

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items/get-work-item?view=azure-devops-rest-7.1&tabs=HTTP
        """
        # https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items/get-work-item?view=azure-devops-rest-7.2&tabs=HTTP#workitemexpand
        params = {
            "$expand": "all"
        }
        
        return self.api.generate_get_request(f"{project_id}/_apis/wit/workItems/{work_item_id}", params=params)
    
    def get_work_item_comments(self, project_id, work_item_id):
        """
        Retrieve all comments for a work item.

        Core REST API: https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-item-comments/list?view=azure-devops-rest-7.1&tabs=HTTP
        """
        params = {
            "$expand": "all"
        }
        return self.api.list_all(f"{project_id}/_apis/wit/workItems/{work_item_id}/comments", params=params)