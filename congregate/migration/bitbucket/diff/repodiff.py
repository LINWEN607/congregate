from json import loads
from os.path import getmtime
from datetime import timedelta
from bson import json_util
from gitlab_ps_utils.api import GitLabApi
from gitlab_ps_utils.misc_utils import get_rollback_log
from gitlab_ps_utils.dict_utils import rewrite_json_list_into_dict, dig
from gitlab_ps_utils.json_utils import read_json_file_into_object

from congregate.migration.diff.basediff import BaseDiffClient
from congregate.migration.bitbucket.repos import ReposClient
from congregate.migration.bitbucket.api.base import BitBucketServerApi
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.helpers.migrate_utils import get_target_project_path, get_full_path_with_parent_namespace
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
        self.gl_groups_api = GroupsApi()
        self.gl_mr_api = MergeRequestsApi()
        self.gl_repository_api = ProjectRepositoryApi()
        self.rollback = rollback
        self.results_path = f"{self.app_path}{'/data/results/project_migration_results.json'}"
        self.results = rewrite_json_list_into_dict(
            read_json_file_into_object(self.results_path))
        self.results_mtime = getmtime(self.results_path)
        self.processes = processes
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
            f"{get_rollback_log(self.rollback)}Generating {self.config.source_type} Repo Diff Report")
        self.log.warning(
            f"Passed since migration time: {timedelta(seconds=start_time - self.results_mtime)}")
        # Drop old collections
        self.drop_diff_report_collections()
        results = self.multi.handle_multi_process_write_to_file_and_return_results(
            self.generate_single_diff_report,
            self.return_only_accuracies,
            self.source_data,
            f"{self.app_path}/data/results/repos_diff.json",
            processes=self.processes)

        for result in results:
            diff_report.update(result)

        # When using stage-wave groups are NOT created
        if not self.config.wave_spreadsheet_path:
            self.log.info(
                f"{get_rollback_log(self.rollback)}Generating {self.config.source_type} Project Diff Report")
            self.generate_parent_diff_report()

        return diff_report

    def generate_parent_diff_report(self):
        self.results_path = f"{self.app_path}{'/data/results/group_migration_results.json'}"
        self.results = rewrite_json_list_into_dict(
            read_json_file_into_object(self.results_path))
        self.results_mtime = getmtime(self.results_path)
        self.source_data = [i for i in read_json_file_into_object(
            f"{self.app_path}/data/staged_groups.json") if i]
        mongo = MongoConnector()
        for parent in self.source_data:
            parent_path = parent["full_path"]
            target_parent_path = get_full_path_with_parent_namespace(
                parent_path)
            if target_parent_path not in self.target_parent_paths:
                self.target_parent_paths.add(target_parent_path)
            else:
                continue
            parent_id = dig(self.results.get(
                target_parent_path), "response", "id")
            if (self.results.get(target_parent_path) or isinstance(self.results.get(target_parent_path), int)) and self.asset_exists(self.gl_groups_api.get_group, parent_id):
                parent_diff = self.handle_parent_endpoints(
                    parent_path, target_parent_path)
                self.insert_diff(parent_diff, mongo,
                                 parent_path, target_parent_path)
                continue
            missing_data = {
                target_parent_path: {
                    "error": "group missing",
                    "overall_accuracy": {
                        "accuracy": 0,
                        "result": "failure"
                    }
                }
            }
            mongo.insert_data(
                f"diff_report_{parent_path}", missing_data)
        mongo.close_connection()

    def generate_single_diff_report(self, project):
        target_project_path = get_target_project_path(project)
        project_id = dig(self.results.get(
            target_project_path), "response", "id")

        # Mongo collection per BBS project with JSON object for each repo
        # Single html report as a result
        # Staged or listed project
        group_namespace = project.get("namespace", "") or dig(
            project, "namespace", "full_path")
        mongo = MongoConnector()
        if (self.results.get(target_project_path) or isinstance(self.results.get(target_project_path), int)) and self.asset_exists(self.gl_projects_api.get_project, project_id):
            project_diff = self.handle_endpoints(project)
            return self.insert_diff(project_diff, mongo, group_namespace, target_project_path)
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

    def insert_diff(self, asset_diff, mongo, group_namespace, target_path):
        diff_report = {}
        diff_report[target_path] = asset_diff
        try:
            diff_report[target_path]["overall_accuracy"] = self.calculate_overall_accuracy(
                diff_report[target_path])
            mongo.insert_data(
                f"diff_report_{group_namespace}", diff_report, bypass_document_validation=True)
            # Convert BSON to JSON
            return loads(json_util.dumps(diff_report))
        except Exception as e:
            self.log.error(
                f"Failed to generate diff for {target_path} with error:\n{e}")

    def handle_parent_endpoints(self, group_namespace, target_parent_path):
        parent_diff = {}
        group = next((g for g in self.source_data if g.get(
            "full_path") == group_namespace), {})

        # Repo parent member permissions - Skip ID field
        group_member_data = [{k: v for k, v in sub.items() if k != "id"}
                             for sub in group.get("members", [])]
        parent_diff["/groups/:id/members"] = self.generate_asset_diff(
            group, "username", group_member_data, self.gl_groups_api.get_all_group_members, obfuscate=True, target_parent_path=target_parent_path)
        return parent_diff

    def handle_endpoints(self, project):
        repo_diff = {}

        if not self.rollback:
            project_key = project["namespace"]
            repo_slug = project["path"]

            # Basic repo stat counts
            repo_diff["Total Number of Merge/Pull Requests"] = self.generate_repo_count_diff(
                project, f"projects/{project_key}/repos/{repo_slug}/pull-requests?state=all", "projects/:id/merge_requests")
            repo_diff["Total Number of Branches"] = self.generate_repo_count_diff(
                project, f"projects/{project_key}/repos/{repo_slug}/branches", "projects/:id/repository/branches")
            repo_diff["Total Number of Tags"] = self.generate_repo_count_diff(
                project, f"projects/{project_key}/repos/{repo_slug}/tags", "projects/:id/repository/tags")
            repo_diff["Total Number of Commits"] = self.generate_repo_count_diff(
                project, f"projects/{project_key}/repos/{repo_slug}/commits", "projects/:id/repository/commits")

            # Pull Requests
            repo_pr_data = list(
                self.repos_api.get_all_repo_pull_requests(project_key, repo_slug))
            transformed_data = self.repos_client.transform_pull_requests(
                repo_pr_data)
            repo_diff["/projects/:id/pull_requests"] = self.generate_asset_diff(
                project, "title", transformed_data, self.gl_mr_api.get_all_project_merge_requests, obfuscate=True)

            # Branches
            repo_branch_data = list(
                self.repos_api.get_all_repo_branches(project_key, repo_slug))
            transformed_data = self.repos_client.transform_branches(
                repo_branch_data)
            repo_diff["/projects/:id/branches"] = self.generate_asset_diff(
                project, "name", transformed_data, self.gl_repository_api.get_all_project_repository_branches, obfuscate=True)

            # Tags
            repo_tag_data = list(
                self.repos_api.get_all_repo_tags(project_key, repo_slug))
            transformed_data = self.repos_client.transform_tags(
                repo_tag_data)
            repo_diff["/projects/:id/tags"] = self.generate_asset_diff(
                project, "name", transformed_data, self.gl_repository_api.get_all_project_repository_tags, obfuscate=True)

            # Commits
            repo_commit_data = list(
                self.repos_api.get_all_repo_commits(project_key, repo_slug))
            transformed_data = self.repos_client.transform_commits(
                repo_commit_data)
            repo_diff["/projects/:id/commits"] = self.generate_asset_diff(
                project, "id", transformed_data, self.gl_repository_api.get_all_project_repository_commits, obfuscate=True)

            # Repo member permissions - Skip ID field
            repo_member_data = [{k: v for k, v in sub.items() if k != "id"}
                                for sub in project.get("members", [])]
            repo_diff["/projects/:id/members"] = self.generate_asset_diff(
                project, "name", repo_member_data, self.gl_projects_api.get_members, obfuscate=True)
        return repo_diff

    def generate_asset_diff(self, asset, sort_key, source_data, gl_endpoint, target_parent_path=None, **kwargs):
        target_namespace = target_parent_path or get_target_project_path(asset)
        limit = target_namespace.rfind("/")
        return self.generate_external_diff(asset, sort_key, source_data, gl_endpoint, parent_group=target_namespace[:limit if limit > 0 else None], **kwargs)

    def generate_repo_count_diff(self, project, bbs_api, gl_api):
        destination_id = self.get_destination_id(project)
        source_count = self.bbs_api.get_total_count(bbs_api)
        destination_count = self.gl_api.get_total_count(
            self.config.destination_host, self.config.destination_token, gl_api.replace(":id", str(destination_id)))
        return self.generate_count_diff(source_count, destination_count)
