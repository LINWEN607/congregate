from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.github.api.repos import ReposApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.migration.github.repos import ReposClient
from congregate.helpers.misc_utils import rewrite_json_list_into_dict, get_rollback_log, dig, deobfuscate, read_json_file_into_object
from congregate.helpers.migrate_utils import get_dst_path_with_namespace
from congregate.helpers.processes import handle_multi_process_write_to_file_and_return_results


class RepoDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated repositories
    '''

    def __init__(self, host, token, staged=False, rollback=False, processes=None):
        super(RepoDiffClient, self).__init__()
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
            "short_id"
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
        results = handle_multi_process_write_to_file_and_return_results(
            self.generate_single_diff_report, self.return_only_accuracies, self.source_data, f"{self.app_path}/data/results/repos_diff.json", processes=self.processes)

        for result in results:
            diff_report.update(result)
        diff_report["project_migration_results"] = self.calculate_overall_stage_accuracy(
            diff_report)

        return diff_report

    def generate_single_diff_report(self, project):
        diff_report = {}
        project_path = get_dst_path_with_namespace(project)
        id = dig(self.results[project_path], "response", "repo_id")
        id = id if id else dig(self.results[project_path], "response", "id")

        if isinstance(self.results.get(project_path), int) and self.results.get(project_path):
            return {
                project_path: {
                    "info": "project already migrated",
                    "overall_accuracy": {
                        "accuracy": 1,
                        "result": "unknown"
                    }
                }
            }
        elif isinstance(self.results.get(project_path), dict) and self.asset_exists(self.gl_projects_api.get_project, id):
            project_diff = self.handle_endpoints(project)
            diff_report[project_path] = project_diff
            try:
                diff_report[project_path]["overall_accuracy"] = self.calculate_overall_accuracy(
                    diff_report[project_path])
                return diff_report
            except Exception:
                self.log.info("Failed to generate diff for %s" % project_path)
        return {
            project_path: {
                "error": "project missing",
                "overall_accuracy": {
                    "accuracy": 0,
                    "result": "failure"
                }
            }
        }

    def handle_endpoints(self, project):
        repo_diff = {}

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
        #         project, "body", transformed_data, self.gl_mr_api.get_merge_request_notes, obfuscate=True)  # How to pass in PR id here??

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
        return self.generate_gh_diff(project, "path_with_namespace", sort_key, source_data, gl_endpoint, parent_group=self.config.dstn_parent_group_path, **kwargs)
