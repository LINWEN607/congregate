from copy import deepcopy
from os.path import getmtime
from datetime import timedelta
from json import dumps as json_dumps
from gitlab_ps_utils.misc_utils import get_rollback_log, safe_json_response
from gitlab_ps_utils.dict_utils import rewrite_json_list_into_dict, dig
from gitlab_ps_utils.json_utils import read_json_file_into_object
from gitlab_ps_utils.api import GitLabApi

from congregate.migration.diff.basediff import BaseDiffClient
from congregate.migration.gitlab import constants
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.helpers.migrate_utils import get_dst_path_with_namespace, get_target_project_path, is_gl_version_older_than, get_stage_wave_paths
from congregate.helpers.utils import to_camel_case


class ProjectDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated projects
    '''

    def __init__(self, staged=False, rollback=False, processes=None):
        super().__init__()
        self.gl_api = GitLabApi(
            app_path=self.app_path, log_name=self.log_name, ssl_verify=self.config.ssl_verify)
        self.projects_api = ProjectsApi()
        self.issues_api = IssuesApi()
        self.mr_api = MergeRequestsApi()
        self.repository_api = ProjectRepositoryApi()
        self.rollback = rollback
        self.results_path = f"{self.app_path}/data/results/project_migration_results.json"
        self.results = rewrite_json_list_into_dict(
            read_json_file_into_object(self.results_path))
        self.results_mtime = getmtime(self.results_path)
        self.processes = processes
        self.keys_to_ignore = constants.PROJECT_DIFF_KEYS_TO_IGNORE
        if staged:
            self.source_data = read_json_file_into_object(
                "%s/data/staged_projects.json" % self.app_path)
        else:
            self.source_data = read_json_file_into_object(
                "%s/data/projects.json" % self.app_path)
        self.source_data = [i for i in self.source_data if i]

    def generate_diff_report(self, start_time):
        diff_report = {}
        self.log.info(
            f"{get_rollback_log(self.rollback)}Generating Project Diff Report")
        self.log.warning(
            f"Passed since migration time: {timedelta(seconds=start_time - self.results_mtime)}")
        results = self.multi.handle_multi_process_write_to_file_and_return_results(
            self.generate_single_diff_report, self.return_only_accuracies, self.source_data, f"{self.app_path}/data/results/project_diff.json", processes=self.processes)

        for result in results:
            diff_report.update(result)
        diff_report["project_migration_results"] = self.calculate_overall_stage_accuracy(
            diff_report)
        return diff_report

    def generate_single_diff_report(self, project):
        diff_report = {}
        project_path = get_dst_path_with_namespace(project)
        if self.results.get(project_path) and type(self.results.get(project_path)) != int and (self.asset_exists(self.projects_api.get_project,
                                                                 self.results[project_path].get("id")) or isinstance(self.results.get(project_path), int)):
            project_diff = self.handle_endpoints(project)
            diff_report[project_path] = project_diff
            try:
                diff_report[project_path]["overall_accuracy"] = self.calculate_overall_accuracy(
                    diff_report[project_path])
                return diff_report
            except Exception as e:
                self.log.info(
                    f"Failed to generate diff for {project_path} with error:\n{e}")
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
        project_diff = {}
        # General endpoint - keep using REST API for this as it's more comprehensive
        project_diff["/projects/:id"] = self.generate_project_diff(
            project, self.projects_api.get_project, obfuscate=True)

        if not self.rollback:
            # Use a single consolidated GraphQL query to fetch all counts
            graphql_data = self.fetch_consolidated_graphql_data(project)
            
            if graphql_data and graphql_data.get("success"):
                # Extract counts from the GraphQL response
                source_data = graphql_data.get("source", {})
                destination_data = graphql_data.get("destination", {})
                
                # Process all the counts we've fetched via GraphQL
                self.log.info(f"Using consolidated GraphQL query results for project stats")
                
                # Commit Counts
                project_diff["Commit Counts"] = {
                    "source": source_data.get("commitCount", 0),
                    "destination": destination_data.get("commitCount", 0),
                    "accuracy": 1.0 if source_data.get("commitCount") == destination_data.get("commitCount") else 0.0,
                    "diff": {"source": source_data.get("commitCount", 0), "destination": destination_data.get("commitCount", 0)} 
                        if source_data.get("commitCount") != destination_data.get("commitCount") else None
                }

                # Branch Counts
                project_diff["Branch Counts"] = {
                    "source": source_data.get("branchCount", 0),
                    "destination": destination_data.get("branchCount", 0),
                    "accuracy": 1.0 if source_data.get("branchCount") == destination_data.get("branchCount") else 0.0,
                    "diff": {"source": source_data.get("branchCount", 0), "destination": destination_data.get("branchCount", 0)} 
                        if source_data.get("branchCount") != destination_data.get("branchCount") else None
                }
                # Merge Requests Counts
                project_diff["Merge Requests Counts"] = {
                    "source": source_data.get("mrCount", 0),
                    "destination": destination_data.get("mrCount", 0),
                    "accuracy": 1.0 if source_data.get("mrCount") == destination_data.get("mrCount") else 0.0,
                    "diff": {"source": source_data.get("mrCount", 0), "destination": destination_data.get("mrCount", 0)}
                        if source_data.get("mrCount") != destination_data.get("mrCount") else None
                }
                
                # Merge Request Comments
                project_diff["Merge Request Comments"] = {
                    "source": source_data.get("mrCommentCount", 0),
                    "destination": destination_data.get("mrCommentCount", 0),
                    "accuracy": 1.0 if source_data.get("mrCommentCount") == destination_data.get("mrCommentCount") else 0.0,
                    "diff": {"source": source_data.get("mrCommentCount", 0), "destination": destination_data.get("mrCommentCount", 0)}
                        if source_data.get("mrCommentCount") != destination_data.get("mrCommentCount") else None
                }
                
                # Issues Counts
                project_diff["Issues Counts"] = {
                    "source": source_data.get("issueCount", 0),
                    "destination": destination_data.get("issueCount", 0),
                    "accuracy": 1.0 if source_data.get("issueCount") == destination_data.get("issueCount") else 0.0,
                    "diff": {"source": source_data.get("issueCount", 0), "destination": destination_data.get("issueCount", 0)}
                        if source_data.get("issueCount") != destination_data.get("issueCount") else None
                }
                
                # Issue Comments
                project_diff["Issue Comments"] = {
                    "source": source_data.get("issueCommentCount", 0),
                    "destination": destination_data.get("issueCommentCount", 0),
                    "accuracy": 1.0 if source_data.get("issueCommentCount") == destination_data.get("issueCommentCount") else 0.0,
                    "diff": {"source": source_data.get("issueCommentCount", 0), "destination": destination_data.get("issueCommentCount", 0)}
                        if source_data.get("issueCommentCount") != destination_data.get("issueCommentCount") else None
                }
            else:
                # Fallback to original methods if GraphQL fails
                self.log.warning("Consolidated GraphQL query failed, falling back to individual queries")
                project_diff["Commit Counts"] = self.generate_project_count_diff(
                    project, "projects/:id/repository/commits")
                project_diff["Merge Requests Counts"] = self.generate_project_count_diff_graphql(
                    project, "merge_requests", "projects/:id/merge_requests")
                project_diff["Issues Counts"] = self.generate_project_count_diff_graphql(
                    project, "issues", "projects/:id/issues")
                project_diff["Merge Request Comments"] = self.generate_nested_project_count_diff_graphql(
                    project, "merge_requests", "notes")
                project_diff["Issue Comments"] = self.generate_nested_project_count_diff_graphql(
                    project, "issues", "notes")

            # CI/CD
            project_diff["/projects/:id/variables"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_variables, obfuscate=True)
            project_diff["/projects/:id/triggers"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_triggers)
            project_diff["/projects/:id/deploy_keys"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_deploy_keys, obfuscate=True)
            project_diff["/projects/:id/pipeline_schedules"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_pipeline_schedules)
            project_diff["/projects/:id/environments"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_environments)
            project_diff["/projects/:id/protected_environments"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_protected_environments)

            # Membership
            project_diff["/projects/:id/members"] = self.generate_project_diff(
                project, self.projects_api.get_members)

            # Repository
            project_diff["/projects/:id/repository/tree"] = self.generate_project_diff(
                project, self.repository_api.get_all_project_repository_tree)
            project_diff["/projects/:id/repository/contributors"] = self.generate_project_diff(
                project, self.repository_api.get_all_project_repository_contributors)
            project_diff["/projects/:id/protected_tags"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_protected_tags)
            project_diff["/projects/:id/forks"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_forks)
            project_diff["/projects/:id/protected_branches"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_protected_branches)
            project_diff["/projects/:id/releases"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_releases)

            # Issue Tracker
            project_diff["/projects/:id/issues"] = self.generate_project_diff(
                project, self.issues_api.get_all_project_issues)
            project_diff["/projects/:id/labels"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_labels)
            project_diff["/projects/:id/milestones"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_milestones)
            project_diff["/projects/:id/boards"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_boards)

            # Misc
            project_diff["/projects/:id/starrers"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_starrers)
            project_diff["/projects/:id/badges"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_badges)
            project_diff["/projects/:id/feature_flags"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_feature_flags)
            project_diff["/projects/:id/custom_attributes"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_custom_attributes)
            project_diff["/projects/:id/registry/repositories"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_registry_repositories)
            project_diff["/projects/:id/hooks"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_hooks)
            project_diff["/projects/:id/snippets"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_snippets)
            project_diff["/projects/:id/wikis"] = self.generate_project_diff(
                project, self.projects_api.get_all_project_wikis)

            if self.config.source_tier not in ["core", "free"]:
                project_diff["/projects/:id/approvals"] = self.generate_project_diff(
                    project, self.projects_api.get_project_level_mr_approval_configuration)
                project_diff["/projects/:id/approval_rules"] = self.generate_project_diff(
                    project, self.projects_api.get_all_project_level_mr_approval_rules)
                project_diff["/projects/:id/push_rule"] = self.generate_project_diff(
                    project, self.projects_api.get_all_project_push_rules)
        
        return project_diff

    def fetch_consolidated_graphql_data(self, project):
        """
        Fetch consolidated project data using GraphQL with pagination for accurate counts
        """
        source_full_path = project['path_with_namespace']
        destination_full_path = get_target_project_path(project)
        
        # Function to fetch data with pagination
        def fetch_with_pagination(host, token, full_path, after_issues="", after_mrs=""):
            query = """
            query ProjectStats($fullPath: ID!, $afterIssues: String, $afterMRs: String) {
            project(fullPath: $fullPath) {
                id
                name
                issues(after: $afterIssues, first: 100) {
                count
                pageInfo {
                    endCursor
                    hasNextPage
                }
                nodes {
                    notes {
                    count
                    }
                }
                }
                mergeRequests(after: $afterMRs, first: 100) {
                count
                pageInfo {
                    endCursor
                    hasNextPage
                }
                nodes {
                    notes {
                    count
                    }
                }
                }
                statistics {
                commitCount
                }
                repository {
                rootRef
                }
            }
            }
            """
            
            variables = {
                "fullPath": full_path,
                "afterIssues": after_issues,
                "afterMRs": after_mrs
            }
            
            response = safe_json_response(self.gl_api.generate_post_request(
                host, token, None, json_dumps({"query": query, "variables": variables}), graphql_query=True
            ))
            
            return response
        
        # Function to fetch branch count using REST API
        def fetch_branch_count(host, token, project_id):
            try:
                count = self.gl_api.get_total_count(
                    host, token, f"projects/{project_id}/repository/branches")
                return count
            except Exception as e:
                self.log.error(f"Error fetching branch count: {str(e)}")
                return 0
        
        # Function to process all pages for a given host/token
        def process_all_pages(host, token, full_path, project_id):
            data = {
                "issueCount": 0,
                "mrCount": 0,
                "issueCommentCount": 0,
                "mrCommentCount": 0,
                "commitCount": 0,
                "branchCount": 0
            }
            
            # First page
            resp = fetch_with_pagination(host, token, full_path)
            if not resp or "data" not in resp or "project" not in resp["data"]:
                self.log.warning(f"Failed to fetch initial GraphQL data for {full_path}")
                return None
            
            project_data = resp["data"]["project"]
            
            # Set the counts that don't need pagination
            data["issueCount"] = dig(project_data, "issues", "count", default=0)
            data["mrCount"] = dig(project_data, "mergeRequests", "count", default=0)
            data["commitCount"] = dig(project_data, "statistics", "commitCount", default=0)
            
            # Fetch branch count separately with REST API
            data["branchCount"] = fetch_branch_count(host, token, project_id)
            
            # Process first page of issues
            for issue in dig(project_data, "issues", "nodes", default=[]):
                data["issueCommentCount"] += dig(issue, "notes", "count", default=0)
            
            # Process first page of merge requests
            for mr in dig(project_data, "mergeRequests", "nodes", default=[]):
                data["mrCommentCount"] += dig(mr, "notes", "count", default=0)
            
            # Paginate through issues if needed
            issues_has_next = dig(project_data, "issues", "pageInfo", "hasNextPage", default=False)
            issues_cursor = dig(project_data, "issues", "pageInfo", "endCursor", default="")
            
            while issues_has_next:
                self.log.info(f"Fetching next page of issues for {full_path}")
                resp = fetch_with_pagination(host, token, full_path, after_issues=issues_cursor, after_mrs="")
                if not resp or "data" not in resp or "project" not in resp["data"]:
                    break
                    
                project_data = resp["data"]["project"]
                
                # Process this page of issues
                for issue in dig(project_data, "issues", "nodes", default=[]):
                    data["issueCommentCount"] += dig(issue, "notes", "count", default=0)
                
                # Update pagination info
                issues_has_next = dig(project_data, "issues", "pageInfo", "hasNextPage", default=False)
                issues_cursor = dig(project_data, "issues", "pageInfo", "endCursor", default="")
            
            # Paginate through merge requests if needed
            mrs_has_next = dig(project_data, "mergeRequests", "pageInfo", "hasNextPage", default=False)
            mrs_cursor = dig(project_data, "mergeRequests", "pageInfo", "endCursor", default="")
            
            while mrs_has_next:
                self.log.info(f"Fetching next page of merge requests for {full_path}")
                resp = fetch_with_pagination(host, token, full_path, after_issues="", after_mrs=mrs_cursor)
                if not resp or "data" not in resp or "project" not in resp["data"]:
                    break
                    
                project_data = resp["data"]["project"]
                
                # Process this page of merge requests
                for mr in dig(project_data, "mergeRequests", "nodes", default=[]):
                    data["mrCommentCount"] += dig(mr, "notes", "count", default=0)
                
                # Update pagination info
                mrs_has_next = dig(project_data, "mergeRequests", "pageInfo", "hasNextPage", default=False)
                mrs_cursor = dig(project_data, "mergeRequests", "pageInfo", "endCursor", default="")
            
            return data
        
        # Get project IDs
        source_id = project["id"]
        destination_id = self.get_destination_id(project)
        
        # Process source and destination
        source_data = process_all_pages(self.config.source_host, self.config.source_token, source_full_path, source_id)
        destination_data = process_all_pages(self.config.destination_host, self.config.destination_token, destination_full_path, destination_id)

        accuracy = self.calculate_count_accuracy(source_data.get("mrCommentCount", 0), 
                                                destination_data.get("mrCommentCount", 0))

        return {
            "success": source_data is not None and destination_data is not None,
            "source": source_data or {},
            "destination": destination_data or {}
        }

    def extract_count_from_graphql(self, project_data, path_to_count):
        """
        Extract counts from GraphQL response and format in the diff structure
        """
        source_data = project_data.get("source")
        destination_data = project_data.get("destination")
        
        # Extract counts using the path (e.g., "repository.branchCount")
        source_count = 0
        destination_count = 0
        
        if source_data:
            parts = path_to_count.split('.')
            temp = source_data
            for part in parts:
                if temp and isinstance(temp, dict) and part in temp:
                    temp = temp[part]
                else:
                    temp = None
                    break
            source_count = temp if isinstance(temp, int) else 0
        
        if destination_data:
            parts = path_to_count.split('.')
            temp = destination_data
            for part in parts:
                if temp and isinstance(temp, dict) and part in temp:
                    temp = temp[part]
                else:
                    temp = None
                    break
            destination_count = temp if isinstance(temp, int) else 0
        
        # Calculate accuracy - either 100% or 0% based on exact match
        accuracy = 1.0 if source_count == destination_count else 0.0
        
        # Create a diff structure if there's a mismatch
        diff = None
        if source_count != destination_count:
            diff = {
                "source": source_count,
                "destination": destination_count
            }
        
        return {
            "source": source_count,
            "destination": destination_count,
            "accuracy": accuracy,
            "diff": diff
        }

    def generate_project_diff(self, project, endpoint, **kwargs):
        return self.generate_diff(project, "path_with_namespace", endpoint,
                                  parent_group=self.config.dstn_parent_group_path, **kwargs)

    def generate_project_count_diff(self, project, api):
        source_id = project["id"]
        destination_id = self.get_destination_id(project)
        source_count = self.gl_api.get_total_count(
            self.config.source_host, self.config.source_token, api.replace(":id", str(source_id)))
        destination_count = self.gl_api.get_total_count(
            self.config.destination_host, self.config.destination_token, api.replace(":id", str(destination_id)))
        
        # Calculate accuracy - either 100% or 0% based on exact match
        accuracy = 1.0 if source_count == destination_count else 0.0
        
        # Create a diff structure if there's a mismatch
        diff = None
        if source_count != destination_count:
            diff = {
                "source": source_count,
                "destination": destination_count
            }
        
        return {
            "source": source_count,
            "destination": destination_count,
            "accuracy": accuracy,
            "diff": diff
        }

    def generate_nested_project_count_diff(self, project, apis):
        source_id = project["id"]
        source_apis = deepcopy(apis)
        source_apis[0] = source_apis[0].replace(":id", str(source_id))
        destination_id = self.get_destination_id(project)
        destination_apis = deepcopy(apis)
        destination_apis[0] = destination_apis[0].replace(
            ":id", str(destination_id))
        source_count = self.gl_api.get_nested_total_count(
            self.config.source_host, self.config.source_token, source_apis)
        destination_count = self.gl_api.get_nested_total_count(
            self.config.destination_host, self.config.destination_token, destination_apis)
        return self.generate_count_diff(source_count, destination_count)

    def generate_project_count_diff_graphql(self, project, entity, api, message=None):
        source_full_path = project['path_with_namespace']
        destination_full_path = get_target_project_path(project)
        formatted_entity = to_camel_case(entity)
        source_count = 0
        destination_count = 0
        if message:
            self.log.info(message)
        # Source count lookup via GraphQL with REST API lookup if instance is older than 17.3
        if gql_resp := safe_json_response(self.gl_api.generate_post_request(
            self.config.source_host, self.config.source_token, None, json_dumps(self.generate_count_query(source_full_path, formatted_entity)), graphql_query=True)):
            if dig(gql_resp, 'data', 'project'):
                source_count = dig(gql_resp, 'data', 'project', formatted_entity, 'count', default=0)
            elif is_gl_version_older_than('17.3', self.config.source_host, self.config.source_token, self.log):
                self.log.warning("GraphQL lookup on source failed. Falling back to REST API")
                source_id = project["id"]
                source_count = self.gl_api.get_total_count(
                    self.config.source_host, self.config.source_token, api.replace(":id", str(source_id)))
        else:
            self.log.warning(f"[{entity}] retrieval for {source_full_path} failed. Skipping.")

        # Destination count lookup via GraphQL with REST API lookup if instance is older than 17.3
        if gql_resp := safe_json_response(self.gl_api.generate_post_request(
            self.config.destination_host, self.config.destination_token, None, json_dumps(self.generate_count_query(destination_full_path, formatted_entity)), graphql_query=True)):
            destination_count = dig(gql_resp, 'data', 'project', formatted_entity, 'count', default=0)
        elif is_gl_version_older_than('17.3', self.config.source_host, self.config.source_token, self.log):
            self.log.warning("GraphQL lookup on destination failed. Falling back to REST API")
            destination_id = self.get_destination_id(project)
            destination_count = self.gl_api.get_total_count(
                self.config.destination_host, self.config.destination_token, api.replace(":id", str(destination_id)))
        else:
            self.log.warning(f"[{entity}] retrieval for {source_full_path} failed. Skipping.")

        # Calculate accuracy
        accuracy = self.calculate_count_accuracy(source_count, destination_count)
        
        # Create a diff structure if there's a mismatch
        diff = None
        if source_count != destination_count:
            diff = {
                "source": source_count,
                "destination": destination_count
            }
        
        return {
            "source": source_count,
            "destination": destination_count,
            "accuracy": accuracy,
            "diff": diff
        }
    
    def generate_nested_project_count_diff_graphql(self, project, primary_entity, secondary_entity):
        source_full_path = project['path_with_namespace']
        destination_full_path = get_target_project_path(project)
        formatted_primary_entity = to_camel_case(primary_entity)
        formatted_secondary_entity = to_camel_case(secondary_entity)
        source_count = self.get_total_nested_count(self.config.source_host, self.config.source_token, source_full_path, formatted_primary_entity, formatted_secondary_entity)
        destination_count = self.get_total_nested_count(self.config.destination_host, self.config.destination_token, destination_full_path, formatted_primary_entity, formatted_secondary_entity)

        # Calculate accuracy - either 100% or 0% based on exact match
        accuracy = self.calculate_count_accuracy(source_count, destination_count)
        
        # Create a diff structure if there's a mismatch
        diff = None
        if source_count != destination_count:
            diff = {
                "source": source_count,
                "destination": destination_count
            }
        
        return {
            "source": source_count,
            "destination": destination_count,
            "accuracy": accuracy,
            "diff": diff
        }    

    def get_total_nested_count(self, host, token, full_path, primary_entity, secondary_entity):
        count = 0
        for data in self.graphql_list_all_outer_nested(host, token, full_path, primary_entity):
            if id := data.get('id'):
                singular_entity = primary_entity.rstrip('s')
                query = self.generate_nested_count_query(id, singular_entity, secondary_entity)
                if resp := safe_json_response(
                    self.gl_api.generate_post_request(host, token, None, data=json_dumps(query), graphql_query=True)):
                        count += dig(resp, 'data', singular_entity, secondary_entity, 'count', default=0)
        return count

    def graphql_list_all_outer_nested(self, host, token, full_path, primary_entity):
        after = ""
        while True:
            query = self.generate_outer_nested_query(full_path, primary_entity, after)
            if resp := safe_json_response(
                    self.gl_api.generate_post_request(host, token, None, data=json_dumps(query), graphql_query=True)):
                yield from dig(resp, 'data', 'project', primary_entity, 'nodes', default=[])
                page_info = dig(resp, 'data', 'project', primary_entity, 'pageInfo', default={})
                if cursor := page_info.get('endCursor'):
                    after = cursor
                if not page_info.get('hasNextPage', False):
                    break

    def generate_count_query(self, full_path, formatted_entity):
        return {
            "query": """
                query {
                    project(fullPath: "%s") {
                        name,
                        %s {
                            count
                        }
                    }
                }
            """ % (full_path, formatted_entity)
        }

    def generate_outer_nested_query(self, full_path, entity, after):
        return {
            "query": """
                query {
                    project(fullPath: "%s") {
                        %s(after:\"%s\") {
                            nodes {
                                id
                            }
                            pageInfo {
                                endCursor
                                hasNextPage
                            }
                        }
                    }
                }
            """ % (full_path, entity, after)
        }

    def generate_nested_count_query(self, id, formatted_parent_entity, formatted_nested_entity):
        return {
            "query": """
                query {
                    %s(id: "%s") {
                        %s {
                            count
                        }
                    }
                }
            """ % (formatted_parent_entity, id, formatted_nested_entity)
        }
