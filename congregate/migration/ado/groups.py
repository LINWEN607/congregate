from gitlab_ps_utils.misc_utils import strip_netloc

from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.migration.ado.base import AzureDevOpsWrapper
from congregate.migration.ado.api.projects import ProjectsApi
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import mongo_connection


class GroupsClient(BaseClass):
    def __init__(self):
        self.api = AzureDevOpsApiWrapper()
        self.base_api = AzureDevOpsWrapper()
        self.projects_api = ProjectsApi()
        super().__init__()

    def retrieve_group_info(self, processes=None):
        for project in self.projects_api.get_all_projects():
            self.handle_retrieving_group(project)

    @mongo_connection
    def handle_retrieving_group(self, project, mongo=None):
        if project:
            count = self.api.get_count(f'{project["id"]}/_apis/git/repositories')
            if count > 1:
                mongo.insert_data(
                    f"groups-{strip_netloc(self.config.source_host)}",
                    self.base_api.format_group(project, mongo))
        else:
            self.log.error("Failed to retrieve project information")
