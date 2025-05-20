from gitlab_ps_utils.misc_utils import strip_netloc

from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.migration.ado.base import AzureDevOpsWrapper
from congregate.migration.ado.api.projects import ProjectsApi
from congregate.migration.ado.api.repositories import RepositoriesApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector


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
        if projects_list:
            self.multi.start_multi_process_stream(
                self.handle_retrieving_project, projects_list, processes=processes)
        else:
            self.multi.start_multi_process_stream(
                self.handle_retrieving_project, self.projects_api.get_all_projects(), processes=processes)

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

