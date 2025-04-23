from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import strip_netloc, is_error_message_present
from congregate.migration.bitbucket_cloud.base import BitBucketCloud
from congregate.helpers.congregate_mdbc import CongregateMongoConnector


class BitbucketCloudReposClient(BitBucketCloud):
    def __init__(self, subset=False):
        super().__init__(subset=subset)
        self.processed_repo_ids = set()  # Track processed repo IDs to avoid duplicates
        
    def retrieve_repo_info(self, processes=None):
        """
        Retrieve repository information from Bitbucket Cloud
        """
        workspace_slug = self.config.src_parent_workspace
        
        if workspace_slug := self.config.src_parent_workspace:

            self.log.info(f"Listing repositories from workspace: {workspace_slug}")

            # Using multi-processing like other clients
            self.multi.start_multi_process_stream_with_args(
                self.handle_retrieving_repos, 
                    self.repos_api.get_all_repos(workspace_slug),
                processes=processes,
                nestable=True
            )
        else:
            self.log.error("No workspace configured. Please set src_parent_workspace in your congregate.conf file.")
            
    def handle_retrieving_repos(self, repo=None, mongo=None):
        """
        Process individual repository data and insert into MongoDB
        """
        error, resp = is_error_message_present(repo)
        if resp and not error:
            # Get and clean the UUID
            uuid = resp.get("uuid", "")
            if uuid and uuid.startswith("{") and uuid.endswith("}"):
                uuid = uuid[1:-1]  # Remove the braces
                
            # Skip if we've already processed this repository
            if uuid in self.processed_repo_ids:
                self.log.info(f"Skipping duplicate repository: {resp.get('slug', 'unknown')}")
                return
                
            # Add to processed repos
            self.processed_repo_ids.add(uuid)
            
            # mongo should be set to None unless this function is being used in a unit test
            if not mongo:
                mongo = CongregateMongoConnector()
                
            # Format and insert the repository
            mongo.insert_data(
                f"projects-{strip_netloc(self.config.source_host)}",
                self.format_repo(resp)
            )
            mongo.close_connection()
        else:
            self.log.error(resp)