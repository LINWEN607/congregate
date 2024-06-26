from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.issue_links import IssueLinksApi
from gitlab_ps_utils.misc_utils import get_dry_log
import time

class IssueLinksClient(BaseClass):
    def __init__(self, DRY_RUN=True):
        self.dry_run = DRY_RUN
        self.issues_api = IssuesApi()
        self.issue_links_api = IssueLinksApi()
        super().__init__()

    def create_project_id_mapping(self, src_projects, dest_projects):
        """
        Create a mapping of source project IDs to destination project IDs based on project names.

        :param: src_projects: (list) List of source GitLab projects
        :param: dest_projects: (list) List of destination GitLab projects
        :return: dict Mapping of source project IDs to destination project IDs
        """
        project_id_mapping = {}
        for src_project in src_projects:
            src_name = src_project['name']
            for dest_project in dest_projects:
                if dest_project['name'] == src_name:
                    project_id_mapping[src_project['id']] = dest_project['id']
                    break
        return project_id_mapping

    def migrate_issue_links(self, src_host, src_token, dest_host, dest_token, src_project_id, dest_project_id):
        """
        Migrate issue links from source project to destination project.

        :param: src_host: (str) Source GitLab host URL
        :param: src_token: (str) Access token to source GitLab instance
        :param: dest_host: (str) Destination GitLab host URL
        :param: dest_token: (str) Access token to destination GitLab instance
        :param: src_project_id: (int) Source GitLab project ID
        :param: dest_project_id: (int) Destination GitLab project ID
        """
        
        for issue in  self.issues_api.get_all_project_issues(src_project_id, src_host, src_token):
            src_issue_iid = issue['iid']

            # Get all issue links for the current issue
            issue_links_response = self.issue_links_api.list_issue_links(src_host, src_token, src_project_id, src_issue_iid)
            issue_links = issue_links_response.json()
            try:
                for link in issue_links:

                    if link:
                        print(f"link found {link}")

                        target_project_id = link['project_id']
                        target_issue_iid = link['iid']
                        link_type = link['link_type']


                        # if not self.dry_run:
                            # Recreate the issue link on the destination side
                        
                        response = self.issue_links_api.create_issue_link(
                            dest_host,
                            dest_token,
                            dest_project_id,
                            src_issue_iid,
                            target_project_id,
                            target_issue_iid,
                            link_type
                        )
                        
                        print(f"response = {response}")

            except Exception as e:
                self.log.error(f"Failed to create link for issue {src_issue_iid}: {e}")
                
                # Introduce a small delay to mitigate race conditions and API rate limits
                time.sleep(0.5)
                # else:
                #     self.log.info(f"{get_dry_log(self.dry_run)} No action performed")
