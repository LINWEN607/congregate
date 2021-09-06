from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.helpers.api import GitLabApi
from congregate.migration.github.api.base import GitHubApi
from congregate.migration.github.api.repos import ReposApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.migration.github.repos import ReposClient
from congregate.helpers.misc_utils import get_rollback_log
from congregate.helpers.dict_utils import rewrite_json_list_into_dict, dig
from congregate.helpers.json_utils import read_json_file_into_object
from congregate.helpers.migrate_utils import get_dst_path_with_namespace


class RepoDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated repositories
    '''

    def __init__(self, host, token, staged=False,
                 rollback=False, processes=None):
        super().__init__()
        self.gl_api = GitLabApi(
            app_path=self.app_path, log_name=self.log_name, ssl_verify=self.config.ssl_verify)
        self.gh_api = GitHubApi(host, token)
        self.repos_api = ReposApi(host, token)
        self.repos_client = ReposClient(host, token)
        self.gl_projects_api = ProjectsApi()
        self.issues_api = IssuesApi()
        self.gl_mr_api = MergeRequestsApi()
        self.gl_repository_api = ProjectRepositoryApi()
        self.rollback = rollback
        self.results = rewrite_json_list_into_dict(read_json_file_into_object(
            f"{self.app_path}{'/data/results/project_migration_results.json'}"))
        self.processes = processes
        self.keys_to_ignore = [
            "_links",
            "last_activity_at",
            "created_at",
            "http_url_to_repo",
            "readme_url",
            "web_url",
            "ssh_url_to_repo",
            "project",
            "forking_access_level",
            "container_expiration_policy",
            "approvals_before_merge",
            "mirror",
            "packages_enabled",
            "external_authorization_classification_label",
            "service_desk_address",
            "service_desk_enabled",
            "marked_for_deletion_at",
            "marked_for_deletion_on",
            "compliance_frameworks",
            "forked_from_project",
            "author_email",
            "author_name",
            "authored_date",
            "committed_date",
            "committer_email",
            "committer_name",
            "created_at",
            "message",
            "parent_ids",
            "title",
            "short_id",
            "id",
            "iid",
            "project_id",
            "source_project_id",
            "target_project_id"
        ]
        if staged:
            self.source_data = read_json_file_into_object(
                "%s/data/staged_projects.json" % self.app_path)
        else:
            self.source_data = read_json_file_into_object(
                "%s/data/projects.json" % self.app_path)
        self.source_data = [i for i in self.source_data if i]

    def generate_diff_report(self):
        diff_report = {}
        self.log.info("{}Generating Repo Diff Report".format(
            get_rollback_log(self.rollback)))
        results = self.multi.handle_multi_process_write_to_file_and_return_results(
            self.generate_single_diff_report, self.return_only_accuracies, self.source_data, f"{self.app_path}/data/results/repos_diff.json", processes=self.processes)

        for result in results:
            diff_report.update(result)
        diff_report["project_migration_results"] = self.calculate_overall_stage_accuracy(
            diff_report)

        return diff_report

    def generate_single_diff_report(self, project):
        diff_report = {}
        if target_namespace := project.get("target_namespace", None):
            project_path = f"{target_namespace}/{project.get('path_with_namespace', '')}".strip(
                "/")
        else:
            project_path = get_dst_path_with_namespace(project)
        if not (project_id := dig(self.results.get(project_path), "response", "repo_id")):
            project_id = dig(self.results.get(project_path), "response", "id")

        project_path_replaced = project_path.replace(".", "_")
        group_namespace = "/".join(project_path_replaced.split("/")[:1])
        mongo = self.connect_to_mongo()
        if self.results.get(project_path) and ((self.asset_exists(self.gl_projects_api.get_project, project_id)) or isinstance(self.results.get(project_path), int)):
            project_diff = self.handle_endpoints(project)
            diff_report[project_path_replaced] = project_diff
            try:
                diff_report[project_path_replaced]["overall_accuracy"] = self.calculate_overall_accuracy(
                    diff_report[project_path_replaced])
                # Cast all keys and values to strings to avoid mongo key validation errors
                cleaned_data = {str(key): str(val)
                                for key, val in (diff_report.copy()).items()}
                mongo.insert_data(
                    f"diff_report_{group_namespace}", cleaned_data, bypass_document_validation=True)
                mongo.close_connection()
                return diff_report
            except Exception as e:
                self.log.error(
                    f"Failed to generate diff for {project_path} with error:\n{e}")
        missing_data = {
            project_path_replaced: {
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
        # Basic Project Stat Counts
        repo_diff["Total Number of Merge Requests"] = self.generate_repo_count_diff(
            project, f"repositories/{project['id']}/pulls", "projects/:id/merge_requests")
        repo_diff["Total Number of Merge Request Comments"] = self.generate_repo_count_diff(
            project, f"repos/{project['namespace']}/{project['path']}/pulls/comments", ["projects/:id/merge_requests", "notes"], bypass_x_total_count=True)
        repo_diff["Total Number of Issues"] = self.generate_repo_count_diff(
            project, f"repositories/{project['id']}/issues", "projects/:id/issues")
        repo_diff["Total Number of Issue Comments"] = self.generate_repo_count_diff(
            project, f"repos/{project['namespace']}/{project['path']}/issues/comments", ["projects/:id/issues", "notes"], bypass_x_total_count=True)
        repo_diff["Total Number of Branches"] = self.generate_repo_count_diff(
            project, f"repositories/{project['id']}/branches", "projects/:id/repository/branches")

        # branches
        repo_branch_data = list(self.repos_api.get_repo_branches(
            project["namespace"], project["name"]))
        transformed_data = self.repos_client.transform_gh_branches(
            repo_branch_data)
        repo_diff["/projects/:id/branches"] = self.generate_repo_diff(
            project, "name", transformed_data, self.gl_repository_api.get_all_project_repository_branches, obfuscate=True)

        # branch permissions

        # pull requests
        repo_pr_data = list(self.repos_api.get_repo_pulls(
            project["namespace"], project["name"]))
        transformed_data = self.repos_client.transform_gh_pull_requests(
            repo_pr_data)
        repo_diff["/projects/:id/pull_requests"] = self.generate_repo_diff(
            project, None, transformed_data, self.gl_mr_api.get_all_project_merge_requests, obfuscate=True)

        # pull requests comments
        # for pr in repo_pr_data:
        #     repo_pr_notes_data = list(self.repos_api.get_repo_pr_comments(project["namespace"], project["name"], pr["number"]))
        #     transformed_data = self.repos_client.transform_gh_pr_comments(repo_pr_notes_data)
        #     repo_diff["/projects/:id/pull_requests_comments"] = self.generate_repo_diff(
        # project, "body", transformed_data,
        # self.gl_mr_api.get_merge_request_notes, obfuscate=True)  # How to
        # pass in PR id here??

        # tags
        repo_tag_data = list(self.repos_api.get_repo_tags(
            project["namespace"], project["name"]))
        transformed_data = self.repos_client.transform_gh_tags(repo_tag_data)
        repo_diff["/projects/:id/tags"] = self.generate_repo_diff(
            project, "name", transformed_data, self.gl_repository_api.get_all_project_repository_tags, obfuscate=True)

        self.keys_to_ignore.append("id")

        # issues
        repo_issue_data = list(self.repos_api.get_repo_issues(
            project["namespace"], project["name"]))
        transformed_data = self.repos_client.transform_gh_issues(
            repo_issue_data)
        repo_diff["/projects/:id/issues"] = self.generate_repo_diff(
            project, None, transformed_data, self.gl_projects_api.get_all_project_issues, obfuscate=True)

        # milestones
        repo_milestone_data = list(self.repos_api.get_repo_milestones(
            project["namespace"], project["name"]))
        transformed_data = self.repos_client.transform_gh_milestones(
            repo_milestone_data)
        repo_diff["/projects/:id/milestones"] = self.generate_repo_diff(
            project, None, transformed_data, self.gl_projects_api.get_all_project_milestones, obfuscate=True)

        # releases
        repo_release_data = list(self.repos_api.get_repo_releases(
            project["namespace"], project["name"]))
        transformed_data = self.repos_client.transform_gh_releases(
            repo_release_data)
        repo_diff["/projects/:id/releases"] = self.generate_repo_diff(
            project, "name", transformed_data, self.gl_projects_api.get_all_project_releases, obfuscate=True)

        if not self.rollback:

            pass

        return repo_diff

    def generate_repo_diff(self, project, sort_key, source_data, gl_endpoint, **kwargs):
        return self.generate_gh_diff(project, "path_with_namespace", sort_key, source_data, gl_endpoint, parent_group=self.config.dstn_parent_group_path or project.get("target_namespace", ""), **kwargs)

    def generate_repo_count_diff(self, project, gh_api, gl_api, bypass_x_total_count=False):
        key = "path_with_namespace"
        destination_id = self.get_destination_id(
            project, key, self.config.dstn_parent_group_path)
        source_count = self.gh_api.get_total_count(
            self.config.source_host,  gh_api)
        if isinstance(gl_api, list):
            gl_api[0] = gl_api[0].replace(":id", str(destination_id))
            destination_count = self.gl_api.get_nested_total_count(
                self.config.destination_host, self.config.destination_token, gl_api, bypass_x_total_count=bypass_x_total_count)
        else:
            destination_count = self.gl_api.get_total_count(
                self.config.destination_host, self.config.destination_token, gl_api.replace(":id", str(destination_id)))
        return self.generate_count_diff(source_count, destination_count)
