from gitlab_ps_utils.misc_utils import get_dry_log, get_timedelta, is_error_message_present, \
    safe_json_response, strip_netloc

from gitlab_ps_utils.json_utils import json_pretty

from congregate.migration.ado.api.projects import ProjectsApi
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector, mongo_connection

class ProjectsClient(BaseClass):
    
    def __init__(self):
        self.projects_api = ProjectsApi()
        super().__init__()

    def retrieve_project_info(self, processes=None):

        for project in self.projects_api.get_all_projects():
                # print(project)
                self.handle_retrieving_project(project)

        # self.multi.start_multi_process_stream_with_args(
        #     self.handle_retrieving_projects, self.projects_api.get_all_projects(), processes=processes)

    @mongo_connection
    def handle_retrieving_project(self, project, mongo=None):

        if project:
            mongo.insert_data(
                f"projects-{strip_netloc(self.config.source_host)}",
                self.format_project(project, mongo))
        else:
            self.log.error("Failed to retrieve project information")

    def format_project(self, project, mongo):
        self.project_groups = {}
        return {
            "name": project["name"],
            "id": project["id"],
            "path": project["id"],
            "full_path": project["id"],
            "visibility": project["visibility"],
            "description": project.get("description", ""),
            "members": [],
            "projects": []
        }
