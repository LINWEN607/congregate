from gitlab_ps_utils.misc_utils import get_dry_log, get_timedelta, is_error_message_present, \
    safe_json_response, strip_netloc

from gitlab_ps_utils.json_utils import json_pretty

from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.migration.ado.api.projects import ProjectsApi
from congregate.migration.ado.api.repositories import RepositoriesApi
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector, mongo_connection

class GroupsClient(BaseClass):
    
    def __init__(self):
        self.api = AzureDevOpsApiWrapper()
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
                    self.api.format_group(project, mongo))
        else:
            self.log.error("Failed to retrieve project information")
