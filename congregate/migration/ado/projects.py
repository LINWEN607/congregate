from gitlab_ps_utils.misc_utils import strip_netloc

from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.migration.ado.base import AzureDevOpsWrapper
from congregate.migration.ado.api.projects import ProjectsApi
from congregate.migration.ado.api.repositories import RepositoriesApi
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import mongo_connection


class ProjectsClient(BaseClass):
    def __init__(self):
        self.api = AzureDevOpsApiWrapper()
        self.base_api = AzureDevOpsWrapper()
        self.projects_api = ProjectsApi()
        self.repositories_api = RepositoriesApi()
        super().__init__()

    def retrieve_project_info(self, processes=None):

        for project in self.projects_api.get_all_projects():
            self.handle_retrieving_project(project)

    @mongo_connection
    def handle_retrieving_project(self, project, mongo=None):
        if not project:
            self.log.error("Failed to retrieve project information")
            return

        count = self.api.get_count(f'{project["id"]}/_apis/git/repositories')
        if count < 1:
            return

        collection_name = f"projects-{strip_netloc(self.config.source_host)}"

        for repository in self.repositories_api.get_all_repositories(project["id"]):
            if repository:
                formatted_project = self.base_api.format_project(project, repository, count, mongo)
                mongo.insert_data(collection_name, formatted_project)


