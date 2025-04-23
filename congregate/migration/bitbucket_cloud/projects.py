from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import strip_netloc, is_error_message_present
from congregate.migration.bitbucket_cloud.base import BitBucketCloud
from congregate.helpers.congregate_mdbc import CongregateMongoConnector


class BitbucketCloudProjectsClient(BitBucketCloud):
    def __init__(self, subset=False):
        super().__init__(subset=subset)
        
    def retrieve_project_info(self, processes=None):
        """
        Retrieve project information from Bitbucket Cloud
        """
        workspace_slug = self.config.src_parent_workspace
        
        if not workspace_slug:
            self.log.error("No workspace configured. Please set src_parent_workspace in your congregate.conf file.")
            return
            
        self.log.info(f"Listing projects from workspace: {workspace_slug}")
        
        # Using multi-processing like other clients
        self.multi.start_multi_process_stream_with_args(
            self.handle_retrieving_projects, 
            self.projects_api.get_all_projects(workspace_slug),
            processes=processes,
            nestable=True
        )
            
    def handle_retrieving_projects(self, project=None, mongo=None):
        """
        Process individual project data and insert into MongoDB
        """
        error, resp = is_error_message_present(project)
        if resp and not error:
            # mongo should be set to None unless this function is being used in a unit test
            if not mongo:
                mongo = CongregateMongoConnector()
                
            # Format and insert the project
            mongo.insert_data(
                f"groups-{strip_netloc(self.config.source_host)}",
                self.format_project(resp, mongo)
            )
            mongo.close_connection()
        else:
            self.log.error(resp)