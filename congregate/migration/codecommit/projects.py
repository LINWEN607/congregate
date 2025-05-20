from gitlab_ps_utils.misc_utils import strip_netloc

from congregate.migration.codecommit.api.base import CodeCommitApiWrapper
from congregate.migration.codecommit.base import CodeCommitWrapper
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import mongo_connection
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
import json


class ProjectsClient(BaseClass):
    def __init__(self):
        self.api = CodeCommitApiWrapper()
        self.base_api = CodeCommitWrapper()
        self.merge_requests_api = MergeRequestsApi()
        super().__init__()

    def retrieve_project_info(self, processes=None):
        self.handle_retrieving_project("CodeCommit")

    @mongo_connection
    def handle_retrieving_project(self, project, mongo=None):
        if not project:
            self.log.error("Failed to retrieve project information")
            return
        repository_list = []
        for repo in self.api.get_all_repositories(project):
            # Save all project repos ID references as part of group metadata
            detailed_repo = self.api.get_repository(project_id=project, repository_name=repo["repositoryName"])
            repository_list.append(detailed_repo)

        count = len(repository_list)
        if count < 1:
            return
        collection_name = f"projects-{strip_netloc(self.config.source_host)}"
        for repository in repository_list:
            if repository:
                formatted_project = self.base_api.format_project(project, repository, count, mongo)
                mongo.insert_data(collection_name, formatted_project)

    def migrate_pull_requests(self, source_project, dstn_project_id, dry_run=False):
        if not dry_run:
            self.log.info(f"Migrating pull requests for project {source_project.get('id')}")
            try:
                count=0
                for pr_num in self.api.get_all_pull_requests(project_id=source_project.get("id"), repository_name=source_project.get("name")):
                    # Convert CodeCommit to GitLab MR format
                    count+=1
                    pr = self.api.get_pull_request(pull_request_id=pr_num, project_id=source_project.get("id"), description=f"Pull request {pr_num} from {source_project.get('name')}")
                    mr_data = {
                        'source_branch': pr['pullRequestTargets'][0]['sourceReference'].replace("refs/heads/", ""),
                        'target_branch': pr['pullRequestTargets'][0]['destinationReference'].replace("refs/heads/", ""),
                        'title': pr['title'],
                        'description': pr['description'],
                        'state': self.pull_request_status(pr),
                        'assignee_ids': []
                    }
                    self.merge_requests_api.create_merge_request(self.config.destination_host, self.config.destination_token, dstn_project_id, mr_data)
                self.log.info(f"Successfully migrated {count} pull requests for {source_project.get('id')}")
            except Exception as e:
                self.log.error(f"Error migrating pull requests for {source_project.get('id')}: {str(e)}")
        else:
            self.log.info(f"Dry run: Skipping pull requests migration for {source_project.get('id')}")

    def pull_request_status(self, pr):
        # CodeCommit: https://docs.aws.amazon.com/cli/latest/reference/codecommit/update-pull-request-status.html
        # GitLab: https://docs.gitlab.com/ee/api/merge_requests.html#list-merge-requests
        if pr["pullRequestStatus"].lower() == "open":
            return "opened"
        elif pr["pullRequestStatus"].lower() == "closed":
            return "closed"
        else:
            return "unknown"
                