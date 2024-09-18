from gitlab_ps_utils.misc_utils import get_dry_log, get_timedelta, is_error_message_present, \
    safe_json_response, strip_netloc

from congregate.migration.ado.api import RepositoriesApi
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector, mongo_connection

class ReposClient(BaseClass):
    
    def __init__(self):
        self.repositories_api = RepositoriesApi()
        super().__init__()

    def retrieve_repo_info(self, project_id, processes=None):
        self.multi.start_multi_process_stream_with_args(
            self.handle_retrieving_repos, self.repositories_api.get_all_repositories(project_id), processes=processes)

    @mongo_connection
    def handle_retrieving_repos(self, repo, mongo=None):
        if repo:
            mongo.insert_data(
                f"projects-{strip_netloc(self.config.source_host)}",
                self.format_repo(repo))
        else:
            self.log.error("Failed to retrieve repository information")

    def format_repo(self, repo):
        formatted_repo = {
            "id": repo.get("id"),
            "name": repo.get("name"),
            "path": repo.get("name"),
            "path_with_namespace": f"{repo.get('project', {}).get('name')}/{repo.get('name')}",
            "description": repo.get("description"),
            "web_url": repo.get("remoteUrl"),
            "visibility": "private" if repo.get("isPrivate") else "public",
            "namespace": {
                "id": repo.get("project", {}).get("id"),
                "name": repo.get("project", {}).get("name"),
                "path": repo.get("project", {}).get("name"),
                "kind": "group",
                "full_path": repo.get("project", {}).get("name")
            }
        }
        return formatted_repo

    def migrate_permissions(self, project, pid):
        # TODO: Implement permission migration for Azure DevOps
        pass

    def correct_repo_description(self, src_repo, pid):
        # TODO: Implement repo description correction for Azure DevOps
        pass

    def transform_pull_requests(self, pull_requests):
        # TODO: Implement pull request transformation for Azure DevOps
        pass

    def transform_branches(self, branches):
        # TODO: Implement branch transformation for Azure DevOps
        pass

    def transform_tags(self, tags):
        # TODO: Implement tag transformation for Azure DevOps
        pass

    def transform_commits(self, commits):
        # TODO: Implement commit transformation for Azure DevOps
        pass
