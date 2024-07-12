from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.issue_links import IssueLinksApi
from gitlab_ps_utils.misc_utils import get_dry_log

class IssueLinksClient(BaseClass):
    def __init__(self, DRY_RUN=True):
        self.dry_run = DRY_RUN
        self.issues_api = IssuesApi()
        self.issue_links_api = IssueLinksApi()
        super().__init__()

    def migrate_issue_links(self, project_id_mapping):
        """
        Migrate issue links from source projects to destination projects using project_id_mapping.

        :param project_id_mapping: (dict) Mapping of source project IDs to destination project IDs
        """
        for src_project_id, dest_project_id in project_id_mapping.items():
            self.migrate_project_issue_links(src_project_id, dest_project_id, project_id_mapping)

    def migrate_project_issue_links(self, src_project_id, dest_project_id, project_id_mapping):
        issues = self.issues_api.get_all_project_issues(src_project_id, self.config.source_host, self.config.source_token)
        for issue in issues:
            self.migrate_issue_links_for_issue(issue, src_project_id, dest_project_id, project_id_mapping)

    def migrate_issue_links_for_issue(self, issue, src_project_id, dest_project_id, project_id_mapping):
        src_issue_iid = issue['iid']
        issue_links = self.get_issue_links(src_project_id, src_issue_iid)
        for link in issue_links:
            self.migrate_single_issue_link(link, src_issue_iid, dest_project_id, project_id_mapping)

    def get_issue_links(self, src_project_id, src_issue_iid):
        issue_links_response = self.issue_links_api.list_issue_links(self.config.source_host, self.config.source_token, src_project_id, src_issue_iid)
        if issue_links_response.status_code != 200:
            self.log.error(f"Failed to list issue links for project {src_project_id}, issue {src_issue_iid}: {issue_links_response.status_code}")
            return []
        return issue_links_response.json()

    def migrate_single_issue_link(self, link, src_issue_iid, dest_project_id, project_id_mapping):
        if link:
            src_target_project_id = link['project_id']
            target_issue_iid = link['iid']
            link_type = link['link_type']
            if not self.dry_run:
                dst_target_project_id = project_id_mapping.get(int(src_target_project_id))
                if dst_target_project_id is None:
                    self.log.warning(f"Skipping link for issue {src_issue_iid}: unable to find destination ID for project {src_target_project_id}")
                    return
                create_response = self.issue_links_api.create_issue_link(
                    self.config.destination_host,
                    self.config.destination_token,
                    dest_project_id,
                    src_issue_iid,
                    dst_target_project_id,
                    target_issue_iid,
                    link_type
                )
                if create_response.status_code != 201:
                    self.log.warning(f"Failed to create issue link for project {dest_project_id}, issue {src_issue_iid}: {create_response.status_code}")
            else:
                self.log.info(f"{get_dry_log(self.dry_run)} No action performed for issue links migration")
