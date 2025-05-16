from gitlab_ps_utils.misc_utils import strip_netloc
from celery import shared_task
from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.migration.ado.base import AzureDevOpsWrapper
from congregate.migration.ado.api.projects import ProjectsApi
from congregate.migration.ado.api.repositories import RepositoriesApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector, mongo_connection


class ProjectsClient(BaseClass):
    def __init__(self, subset: bool = False):
        self.subset = subset
        self.api = AzureDevOpsApiWrapper()
        self.base_api = AzureDevOpsWrapper()
        self.projects_api = ProjectsApi()
        self.repositories_api = RepositoriesApi()
        self.users_api = UsersApi()
        super().__init__()

    def retrieve_project_info(self, processes=None, projects_list=None):
        if projects_list is not None:
            projects_iter = projects_list
        else:
            projects_iter = self.projects_api.get_all_projects()
        if self.config.direct_transfer:
            self.log.info("Direct transfer enabled - queuing ADO projects via Celery")
            for project in projects_iter:
                handle_retrieving_ado_projects_task.delay(project)
        else:
            self.log.info("Direct transfer disabled - using multiprocessing for ADO projects")
            self.multi.start_multi_process_stream(
                self.handle_retrieving_project, projects_iter, processes=processes)

    def handle_retrieving_project(self, project, mongo=None):
        if not mongo:
            mongo = CongregateMongoConnector()
        if not project:
            self.log.error("Failed to retrieve project information")
            return
        count = self.api.get_count(f'{project["id"]}/_apis/git/repositories')
        if count < 1:
            return
        collection_name = f"projects-{strip_netloc(self.config.source_host)}"
        for repository in self.repositories_api.get_all_repositories(project["id"]):
            if (
                repository 
                and repository.get("isDisabled", False) is False
                and repository.get("defaultBranch")
            ):
                formatted_project = self.base_api.format_project(project, repository, count, mongo)
                mongo.insert_data(collection_name, formatted_project)
        mongo.close_connection()


@shared_task(name='retrieve-ado-projects')
@mongo_connection
def handle_retrieving_ado_projects_task(project, mongo=None):
    project_client = ProjectsClient()
    project_client.log.info("Handling ADO project via Celery task")
    if project:
        project_client.handle_retrieving_project(project, mongo)
    else:
        project_client.log.error(f"Failed to process ADO project data. Was provided [{project}]")
