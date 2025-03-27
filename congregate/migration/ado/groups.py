from gitlab_ps_utils.misc_utils import strip_netloc

from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.migration.ado.base import AzureDevOpsWrapper
from congregate.migration.ado.api.projects import ProjectsApi
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector


class GroupsClient(BaseClass):
    def __init__(self):
        self.api = AzureDevOpsApiWrapper()
        self.base_api = AzureDevOpsWrapper()
        self.projects_api = ProjectsApi()
        super().__init__()

    def retrieve_group_info(self, processes=None, projects_list=None):
        if projects_list:
            self.multi.start_multi_process_stream(self.handle_retrieving_group, 
                projects_list, processes=processes)
        else:
            self.multi.start_multi_process_stream(self.handle_retrieving_group, 
                self.projects_api.get_all_projects(), processes=processes)

    def handle_retrieving_group(self, project, mongo=None):
        if not mongo:
            mongo = CongregateMongoConnector()
        if project:
            count = self.api.get_count(f'{project["id"]}/_apis/git/repositories')
            if count > 1:
                mongo.insert_data(
                    f"groups-{strip_netloc(self.config.source_host)}",
                    self.base_api.format_group(project, mongo))
        else:
            self.log.error("Failed to retrieve project information")
        mongo.close_connection()
