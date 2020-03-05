from types import GeneratorType
from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.variables import VariablesClient
from congregate.helpers.misc_utils import rewrite_json_list_into_dict, get_rollback_log


class ProjectDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated projects
    '''

    def __init__(self, results_path, staged=False):
        super(ProjectDiffClient, self).__init__()
        self.projects_api = ProjectsApi()
        self.variables_api = VariablesClient()
        self.results = rewrite_json_list_into_dict(
            self.load_json_data("{0}{1}".format(self.app_path, results_path)))
        self.keys_to_ignore = [
            "id",
            "_links",
            "last_activity_at",
            "created_at",
            "http_url_to_repo",
            "readme_url",
            "web_url",
            "ssh_url_to_repo",
            "project"
        ]

        if staged:
            self.source_data = self.load_json_data(
                "%s/data/stage.json" % self.app_path)
        else:
            self.source_data = self.load_json_data(
                "%s/data/project_json.json" % self.app_path)

    def generate_diff_report(self, rollback=False):
        diff_report = {}
        self.log.info("{}Generating Project Diff Report".format(
            get_rollback_log(rollback)))

        for project in self.source_data:
            if self.results.get(project["path_with_namespace"]):
                project_diff = self.handle_endpoints(project)
                diff_report[project["path_with_namespace"]] = project_diff
                diff_report[project["path_with_namespace"]]["overall_accuracy"] = self.calculate_overall_accuracy(
                    diff_report[project["path_with_namespace"]])
            else:
                diff_report[project["path_with_namespace"]] = {
                    "error": "project missing",
                    "overall_accuracy": {
                        "accuracy": 0,
                        "result": "failure"
                    }
                }

        diff_report["project_migration_results"] = self.calculate_overall_stage_accuracy(
            diff_report)

        return diff_report

    def handle_endpoints(self, project):
        project_diff = {}
        # General endpoint
        project_diff["/projects/:id"] = self.generate_diff(
            project, self.projects_api.get_project, obfuscate=True)
        # CI/CD
        project_diff["/projects/:id/variables"] = self.generate_diff(
            project, self.variables_api.get_variables, obfuscate=True, var_type="project")
        project_diff["/projects/:id/triggers"] = self.generate_diff(
            project, self.projects_api.get_all_project_triggers)
        project_diff["/projects/:id/deploy_keys"] = self.generate_diff(
            project, self.projects_api.get_all_project_deploy_keys, obfuscate=True)
        project_diff["/projects/:id/pipeline_schedules"] = self.generate_diff(
            project, self.projects_api.get_all_project_pipeline_schedules)
        project_diff["/projects/:id/environments"] = self.generate_diff(
            project, self.projects_api.get_all_environments)
        project_diff["/projects/:id/jobs"] = self.generate_diff(
            project, self.projects_api.get_all_project_jobs)

        # Membership
        project_diff["/projects/:id/members"] = self.generate_diff(
            project, self.projects_api.get_members)
        project_diff["/projects/:id/members/all"] = self.generate_diff(
            project, self.projects_api.get_all_project_members_incl_inherited)
        project_diff["/projects/:id/users"] = self.generate_diff(
            project, self.projects_api.get_all_project_users)
        
        # Merge request approvers
        project_diff["/projects/:id/approvals"] = self.generate_diff(
            project, self.projects_api.get_all_project_approval_configuration)
        project_diff["/projects/:id/approval_rules"] = self.generate_diff(
            project, self.projects_api.get_all_project_approval_rules)
        
        # Repository
        project_diff["/projects/:id/forks"] = self.generate_diff(
            project, self.projects_api.get_all_project_forks)
        project_diff["/projects/:id/protected_branches"] = self.generate_diff(
            project, self.projects_api.get_all_project_protected_branches)
        project_diff["/projects/:id/push_rule"] = self.generate_diff(
            project, self.projects_api.get_all_project_push_rules)
        project_diff["/projects/:id/releases"] = self.generate_diff(
            project, self.projects_api.get_all_project_releases)

        # Issue Tracker
        project_diff["/projects/:id/issues"] = self.generate_diff(
            project, self.projects_api.get_all_project_issues)
        project_diff["/projects/:id/labels"] = self.generate_diff(
            project, self.projects_api.get_all_project_labels)
        project_diff["/projects/:id/milestones"] = self.generate_diff(
            project, self.projects_api.get_all_project_milestones)
        
        # Misc
        project_diff["/projects/:id/starrers"] = self.generate_diff(
            project, self.projects_api.get_all_project_starrers)
        project_diff["/projects/:id/badges"] = self.generate_diff(
            project, self.projects_api.get_all_project_badges)
        project_diff["/projects/:id/feature_flags"] = self.generate_diff(
            project, self.projects_api.get_all_project_feature_flags)
        project_diff["/projects/:id/custom_attributes"] = self.generate_diff(
            project, self.projects_api.get_all_project_custom_attributes)
        project_diff["/projects/:id/registry/repositories"] = self.generate_diff(
            project, self.projects_api.get_all_project_registry_repositories)
        
        return project_diff


    def generate_diff(self, project, endpoint, critical_key=None, obfuscate=False, **kwargs):
        source_project_data = self.generate_cleaned_instance_data(
            endpoint(project["id"], self.config.source_host, self.config.source_token, **kwargs))
        if source_project_data:
            if self.results.get(project["path_with_namespace"].lower()) is not None:
                project["path_with_namespace"] = project["path_with_namespace"].lower()
            if self.results.get(project["path_with_namespace"]) is not None:
                if isinstance(self.results[project["path_with_namespace"]], dict):
                    destination_project_id = self.results[project["path_with_namespace"]]["id"]
                    destination_project_data = self.generate_cleaned_instance_data(
                        endpoint(destination_project_id, self.config.destination_host, self.config.destination_token, **kwargs))
                else:
                    destination_project_data = {
                        "error": "project missing"
                    }
            else:
                destination_project_data = self.generate_empty_data(
                    source_project_data)

            return self.diff(source_project_data, destination_project_data, critical_key=critical_key, obfuscate=obfuscate)

        return self.empty_diff()

    def generate_empty_data(self, source):
        if isinstance(source, list):
            return [
                {
                    'error': 'project is missing'
                }
            ]
        return {
            'error': 'project is missing'
        }

    def generate_cleaned_instance_data(self, instance_data):
        if isinstance(instance_data, GeneratorType):
            try:
                instance_data = self.ignore_keys(list(instance_data))
            except TypeError:
                return []
        else:
            instance_data = self.ignore_keys(instance_data.json())
        return instance_data
