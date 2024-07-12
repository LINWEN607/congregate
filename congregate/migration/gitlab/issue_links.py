from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.issue_links import IssueLinksApi
from gitlab_ps_utils.misc_utils import is_error_message_present

class IssueLinksClient(BaseClass):
    def __init__(self, DRY_RUN=True):
        self.dry_run = DRY_RUN
        self.issues_api = IssuesApi()
        self.issue_links_api = IssueLinksApi()
        super().__init__()

    def migrate_issue_links(self, project_id_mapping):
        """
        Migrate issue links from source projects to destination projects using project_id_mapping.

        :param: project_id_mapping: (dict) Mapping of source project IDs to destination project IDs
        """
        
        for src_project_id, dest_project_id in project_id_mapping.items():
            for issue in self.issues_api.get_all_project_issues(src_project_id, self.config.source_host, self.config.source_token):
                src_issue_iid = issue['iid']
                # Get all issue links for the current issue
                issue_links_response = self.issue_links_api.list_issue_links(self.config.source_host, self.config.source_token, src_project_id, src_issue_iid)
                issue_links = issue_links_response.json()
                for link in issue_links:
                    if link:
                        src_target_project_id = link['project_id']
                        target_issue_iid = link['iid']
                        link_type = link['link_type']
                        if not self.dry_run:
                            # Translate source project ID to destination project ID
                            dst_target_project_id = project_id_mapping.get(str(src_target_project_id))
                            if dst_target_project_id is None:
                                self.log.info(f"Skipping link for issue {src_issue_iid}: unable to find destination ID for project {src_target_project_id}")
                                continue
                            # Recreate the issue link on the destination side
                            self.issue_links_api.create_issue_link(
                                self.config.destination_host,
                                self.config.destination_token,
                                dest_project_id,
                                src_issue_iid,
                                dst_target_project_id,
                                target_issue_iid,
                                link_type
                            )
