from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import strip_netloc, is_error_message_present
from congregate.helpers.migrate_utils import get_subset_list, check_list_subset_input_file_path
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.base import BitBucketServer
from congregate.helpers.mdbc import MongoConnector


class ProjectsClient(BitBucketServer):
    def __init__(self, subset=False, skip_project_members=False, skip_group_members=False):
        self.projects_api = ProjectsApi()
        super().__init__()
        self.subset = subset
        self.skip_project_members = skip_project_members
        self.skip_group_members = skip_group_members

    def set_user_groups(self, groups):
        self.user_groups = groups

    def retrieve_project_info(self, processes=None):
        if self.subset:
            subset_path = check_list_subset_input_file_path()
            self.log.info(
                f"Listing subset of {self.config.source_host} projects from '{subset_path}'")
            self.multi.start_multi_process_stream_with_args(
                self.handle_projects_subset, get_subset_list(), processes=processes, nestable=True)
        else:
            self.multi.start_multi_process_stream_with_args(
                self.handle_retrieving_projects, self.projects_api.get_all_projects(), processes=processes, nestable=True)

    def handle_projects_subset(self, project, project_key=None):
        # e.g. https://www.bitbucketserverexample.com/projects/TEST"
        project_key = project_key or project.split("/")[4]
        try:
            project_json = self.projects_api.get_project(project_key)
            self.handle_retrieving_projects(project_json)
        except RequestException as re:
            self.log.error(
                f"Failed to GET project '{project_key}', with error:\n{re}")

    def handle_retrieving_projects(self, project, mongo=None):
        error, resp = is_error_message_present(project)
        if resp and not error:
            # mongo should be set to None unless this function is being used in a
            # unit test
            if not mongo:
                mongo = MongoConnector()
            mongo.insert_data(
                f"groups-{strip_netloc(self.config.source_host)}",
                self.format_project(resp, mongo))
            mongo.close_connection()
        else:
            self.log.error(resp)
