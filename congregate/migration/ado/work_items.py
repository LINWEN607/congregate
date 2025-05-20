import json
from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.helpers.base_class import BaseClass

class WorkItemsClient(BaseClass):
    def __init__(self, subset=False):
        self.subset = subset
        self.ado_api = AzureDevOpsApiWrapper()
        self.headers = {}
        super().__init__()

    def get_all_work_items(self, project):
        """
        Retrieves all work items for a given Azure DevOps project.

        Args:
            project (dict): Dictionary containing 'project_id' and 'name' keys.

        Returns:
            list: List of work items, empty if none found.
        """
        project_id = project.get('project_id')
        project_name = project.get('name')
        if not project_id or not project_name:
            return []

        wiql_query = (
            "SELECT [System.Id], [System.Title], [System.State] "
            "FROM WorkItems WHERE [System.TeamProject] = '{}'".format(project_name)
        )
        payload = json.dumps({"query": wiql_query})

        try:
            response = self.ado_api.generate_post_request(
                f'{project_id}/_apis/wit/wiql', data=payload
            )
            response.raise_for_status()
            work_items = response.json().get('workItems', [])
        except Exception:
            work_items = []

        return work_items
