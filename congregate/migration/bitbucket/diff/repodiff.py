from os.path import getmtime
from datetime import timedelta
from gitlab_ps_utils.api import GitLabApi
from gitlab_ps_utils.misc_utils import get_rollback_log
from gitlab_ps_utils.dict_utils import rewrite_json_list_into_dict, dig
from gitlab_ps_utils.json_utils import read_json_file_into_object

from congregate.migration.gitlab.diff.basediff import BaseDiffClient
# from congregate.migration.bitbucket import constants
from congregate.migration.bitbucket.repos import ReposClient
from congregate.migration.bitbucket.api.base import BitBucketServerApi
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.helpers.migrate_utils import get_target_project_path
from congregate.helpers.mdbc import MongoConnector


class RepoDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated repositories
    '''

    def __init__(self, staged=False, rollback=False, processes=None):
        super().__init__()
        self.gl_api = GitLabApi(
            app_path=self.app_path, log_name=self.log_name, ssl_verify=self.config.ssl_verify)
        self.bbs_api = BitBucketServerApi()
        self.repos_api = ReposApi()
        self.repos_client = ReposClient()
        self.gl_projects_api = ProjectsApi()
        self.gl_mr_api = MergeRequestsApi()
        self.gl_repository_api = ProjectRepositoryApi()
        self.rollback = rollback
        self.results_path = f"{self.app_path}{'/data/results/project_migration_results.json'}"
        self.results = rewrite_json_list_into_dict(
            read_json_file_into_object(self.results_path))
        self.results_mtime = getmtime(self.results_path)
        self.processes = processes
        # self.keys_to_ignore = constants.BBS_KEYS_TO_IGNORE
        if staged:
            self.source_data = read_json_file_into_object(
                f"{self.app_path}/data/staged_projects.json")
        else:
            self.source_data = read_json_file_into_object(
                f"{self.app_path}/data/projects.json")
        self.source_data = [i for i in self.source_data if i]

    def generate_diff_report(self, start_time):
        diff_report = {}
        self.log.info(
            f"{get_rollback_log(self.rollback)}Generating Repo Diff Report")
        self.log.warning(
            f"Passed since migration time: {timedelta(seconds=start_time - self.results_mtime)}")
        results = self.multi.handle_multi_process_write_to_file_and_return_results(
            self.generate_single_diff_report,
            self.return_only_accuracies,
            self.source_data,
            f"{self.app_path}/data/results/repos_diff.json",
            processes=self.processes)

        for result in results:
            diff_report.update(result)
        diff_report["project_migration_results"] = self.calculate_overall_stage_accuracy(
            diff_report)

        return diff_report

    def generate_single_diff_report(self, project):
        diff_report = {}
        target_project_path = get_target_project_path(project)

        project_id = dig(self.results.get(
            target_project_path), "response", "id")

        # Mongo restriction with storing "." as key
        # project_path_replaced = project_path.replace(".", "_")

        # Mongo collection per BBS project with JSON object for each repo
        # Single html report as a result
        # group_namespace = "/".join(target_project_path.split("/")[:1])
        group_namespace = project.get("namespace", "")
        mongo = MongoConnector()
        if self.results.get(target_project_path) and self.asset_exists(self.gl_projects_api.get_project, project_id):
            project_diff = self.handle_endpoints(project)
            diff_report[target_project_path] = project_diff
            try:
                diff_report[target_project_path]["overall_accuracy"] = self.calculate_overall_accuracy(
                    diff_report[target_project_path])
                # Cast all keys and values to strings to avoid mongo key validation errors
                cleaned_data = {str(key): str(val)
                                for key, val in (diff_report.copy()).items()}
                mongo.insert_data(
                    f"diff_report_{group_namespace}", cleaned_data, bypass_document_validation=True)
                mongo.close_connection()
                return diff_report
            except Exception as e:
                self.log.error(
                    f"Failed to generate diff for {target_project_path} with error:\n{e}")
        missing_data = {
            target_project_path: {
                "error": "project missing",
                "overall_accuracy": {
                    "accuracy": 0,
                    "result": "failure"
                }
            }
        }
        mongo.insert_data(
            f"diff_report_{group_namespace}", missing_data.copy())
        mongo.close_connection()
        return missing_data

    def handle_endpoints(self, project):
        repo_diff = {}

        if not self.rollback:
            project_key = project["namespace"]
            repo_slug = project["path"]
            # Basic Project Stat Counts
            repo_diff["Total Number of Merge/Pull Requests"] = self.generate_repo_count_diff(
                project, f"projects/{project_key}/repos/{repo_slug}/pull-requests?state=all", "projects/:id/merge_requests")
            # repo_diff["Total Number of Merge Request Comments"] = self.generate_repo_count_diff(
            #     project, f"repos/{project['namespace']}/{project['path']}/pulls/comments", ["projects/:id/merge_requests", "notes"], bypass_x_total_count=True)
            repo_diff["Total Number of Branches"] = self.generate_repo_count_diff(
                project, f"projects/{project_key}/repos/{repo_slug}/branches", "projects/:id/repository/branches")
            repo_diff["Total Number of Tags"] = self.generate_repo_count_diff(
                project, f"projects/{project_key}/repos/{repo_slug}/tags", "projects/:id/repository/tags")
            repo_diff["Total Number of Commits"] = self.generate_repo_count_diff(
                project, f"projects/{project_key}/repos/{repo_slug}/commits", "projects/:id/repository/commits")

            # pull requests
            repo_pr_data = list(
                self.repos_api.get_all_repo_pull_requests(project_key, repo_slug))
            transformed_data = self.repos_client.transform_pull_requests(
                repo_pr_data)
            repo_diff["/projects/:id/pull_requests"] = self.generate_repo_diff(
                project, "title", transformed_data, self.gl_mr_api.get_all_project_merge_requests, obfuscate=True)

            # pull requests comments
            # for pr in repo_pr_data:
            #     repo_pr_notes_data = list(self.repos_api.get_repo_issue_comments(project["namespace"], project["name"], pr["number"]))
            #     transformed_data = self.repos_client.transform_gh_pr_comments(repo_pr_notes_data)
            #     repo_diff["/projects/:id/pull_requests_comments"] = self.generate_repo_diff(
            # project, "body", transformed_data,
            # self.gl_mr_api.get_merge_request_notes, obfuscate=True)  # How to
            # pass in PR id here??

            # branches
            repo_branch_data = list(
                self.repos_api.get_all_repo_branches(project_key, repo_slug))
            transformed_data = self.repos_client.transform_branches(
                repo_branch_data)
            repo_diff["/projects/:id/branches"] = self.generate_repo_diff(
                project, "name", transformed_data, self.gl_repository_api.get_all_project_repository_branches, obfuscate=True)

            # TODO: branch permissions

            # tags
            repo_tag_data = list(
                self.repos_api.get_all_repo_tags(project_key, repo_slug))
            transformed_data = self.repos_client.transform_tags(
                repo_tag_data)
            repo_diff["/projects/:id/tags"] = self.generate_repo_diff(
                project, "name", transformed_data, self.gl_repository_api.get_all_project_repository_tags, obfuscate=True)

            # commits
            repo_commit_data = list(
                self.repos_api.get_all_repo_commits(project_key, repo_slug))
            transformed_data = self.repos_client.transform_commits(
                repo_commit_data)
            repo_diff["/projects/:id/commits"] = self.generate_repo_diff(
                project, "id", transformed_data, self.gl_repository_api.get_all_project_repository_commits, obfuscate=True)
        return repo_diff

    def generate_repo_diff(self, project, sort_key, source_data, gl_endpoint, **kwargs):
        return self.generate_bbs_diff(project, sort_key, source_data, gl_endpoint, parent_group=get_target_project_path(project)[:-1].strip("/"), **kwargs)

    def generate_repo_count_diff(self, project, bbs_api, gl_api):
        destination_id = self.get_destination_id(project)
        source_count = self.bbs_api.get_total_count(bbs_api)
        destination_count = self.gl_api.get_total_count(
            self.config.destination_host, self.config.destination_token, gl_api.replace(":id", str(destination_id)))
        return self.generate_count_diff(source_count, destination_count)
