from gitlab_ps_utils.misc_utils import strip_netloc

from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.migration.ado.base import AzureDevOpsWrapper
from congregate.migration.ado.api.projects import ProjectsApi
from congregate.migration.ado.api.repositories import RepositoriesApi
from congregate.migration.ado.api.pull_requests import PullRequestsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector


class ProjectsClient(BaseClass):
    def __init__(self, subset: bool = False):
        self.subset = subset
        self.api = AzureDevOpsApiWrapper()
        self.base_api = AzureDevOpsWrapper()
        self.projects_api = ProjectsApi()
        self.repositories_api = RepositoriesApi()
        self.pull_requests_api = PullRequestsApi()
        self.users_api = UsersApi()
        self.merge_requests_api = MergeRequestsApi()
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
            if repository and repository.get("isDisabled") is False and repository.get("size") > 0:
                formatted_project = self.base_api.format_project(project, repository, count, mongo)
                mongo.insert_data(collection_name, formatted_project)
        mongo.close_connection()

    def migrate_pull_requests(self, source_project, dstn_project_id, dry_run=False):
        if not dry_run:
            self.log.info(f"Migrating pull requests for project {source_project.get('project_id')}")
            try:
                count=0
                for pr in self.pull_requests_api.get_all_pull_requests(project_id=source_project.get("project_id"), repository_id=source_project.get("id")):
                    # Convert Azure DevOps PR to GitLab MR format
                    count+=1
                    mr_data = {
                        'source_branch': pr['sourceRefName'].replace("refs/heads/", ""),
                        'target_branch': pr['targetRefName'].replace("refs/heads/", ""),
                        'title': pr['title'],
                        'description': pr['description'],
                        'state': self.pull_request_status(pr),
                        'assignee_ids': [] if self.subset else self.add_assignee_ids([], source_project)
                    }
                    self.merge_requests_api.create_merge_request(self.config.destination_host, self.config.destination_token, dstn_project_id, mr_data)
                self.log.info(f"Successfully migrated {count} pull requests for {source_project.get('project_id')}")
            except Exception as e:
                self.log.error(f"Error migrating pull requests for {source_project.get('project_id')}: {str(e)}")
        else:
            self.log.info(f"Dry run: Skipping pull requests migration for {source_project.get('project_id')}")

    def pull_request_status(self, pr):
        # ADO: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-requests/get-pull-request-by-id?view=azure-devops-rest-7.1&tabs=HTTP#pullrequeststatus
        # GitLab: https://docs.gitlab.com/ee/api/merge_requests.html#list-merge-requests
        if pr["status"] == "active":
            return "opened"
        elif pr["status"] == "completed":
            return "merged"
        elif pr["status"] == "abandoned":
            return "closed"
        else:
            return "unknown"

    def add_assignee_ids(self, assignee_ids, source_project):
        assignee_ids = []
        for username in source_project["members"]:
            user_email = username["email"]
            for user in self.users_api.search_for_user_by_email(self.config.destination_host, self.config.destination_token, user_email):
                assignee_ids.append(user.get("id"))
        return assignee_ids
