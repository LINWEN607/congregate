from gitlab_ps_utils.misc_utils import strip_netloc
from celery import shared_task
from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.migration.ado.base import AzureDevOpsWrapper
from congregate.migration.ado.api.projects import ProjectsApi
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector, mongo_connection


class GroupsClient(BaseClass):
    def __init__(self):
        self.api = AzureDevOpsApiWrapper()
        self.base_api = AzureDevOpsWrapper()
        self.projects_api = ProjectsApi()
        super().__init__()

    def retrieve_group_info(self, processes=None, projects_list=None):
        projects = projects_list if projects_list else self.projects_api.get_all_projects()
        if self.config.direct_transfer:
            self.log.info("Direct transfer enabled - queuing ADO groups via Celery")
            for project in projects:
                handle_retrieving_ado_groups_task.delay(project)
        else:
            self.log.info("Direct transfer disabled - using multiprocessing for ADO groups")
            self.multi.start_multi_process_stream(
                self.handle_retrieving_group,
                projects,
                processes=processes
            )

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


@shared_task(name='retrieve-ado-groups')
@mongo_connection
def handle_retrieving_ado_groups_task(project, mongo=None):
    grp_client = GroupsClient()
    if project:
        grp_client.handle_retrieving_group(project, mongo)
    else:
        grp_client.log.error(f"Failed to process ADO group data. Was provided [{project}]")