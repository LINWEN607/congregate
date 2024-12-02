from gitlab_ps_utils.misc_utils import strip_netloc

from congregate.migration.codecommit.api.base import CodeCommitApiWrapper
from congregate.migration.codecommit.base import CodeCommitWrapper
# from congregate.migration.ado.api.projects import ProjectsApi
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import mongo_connection


class GroupsClient(BaseClass):
    def __init__(self):
        self.api = CodeCommitApiWrapper()
        self.base_api = CodeCommitWrapper()
        super().__init__()

    def retrieve_group_info(self, processes=None):
        self.handle_retrieving_group("CodeCommit")

    @mongo_connection
    def handle_retrieving_group(self, project, mongo=None):
        if not project:
            self.log.error("Failed to retrieve project information")
            return
        repository_list = []
        for repo in self.api.get_all_repositories(project):
            # Save all project repos ID references as part of group metadata
            detailed_repo = self.api.get_repository(project_id=project, repository_name=repo["repositoryName"])
            repository_list.append(detailed_repo)

        count = len(repository_list)
        if count > 1:
                mongo.insert_data(
                    f"groups-{strip_netloc(self.config.source_host)}",
                    self.base_api.format_group(project,repository_list, mongo))
        else:
                self.log.error("Failed to retrieve project information")
        

