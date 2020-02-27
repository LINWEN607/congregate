from types import GeneratorType
from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab.api.environments import EnvironmentsApi
from congregate.helpers.misc_utils import rewrite_json_list_into_dict

class ProjectDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated projects
    '''
    def __init__(self, results_file, staged=False):
        super(ProjectDiffClient, self).__init__()
        self.projects_api = ProjectsApi()
        self.variables_api = VariablesClient()
        self.environments_api = EnvironmentsApi()
        self.results = rewrite_json_list_into_dict(self.load_json_data(results_file))
        self.keys_to_ignore = [
            "id",
            "_links",
            "last_activity_at",
            "created_at",
            "http_url_to_repo",
            "readme_url",
            "web_url",
            "ssh_url_to_repo"
        ]

        if staged:
            self.source_data = self.load_json_data("%s/data/stage.json" % self.app_path)
        else:
            self.source_data = self.load_json_data("%s/data/project_json.json" % self.app_path)

    def generate_project_diff_report(self):
        diff_report = {}
        self.log.info("Generating Project Diff Report")
        
        for project in self.source_data:
            if self.results.get(project["path_with_namespace"]):
                project_diff = {}
                project_diff["/projects/:id"] = self.generate_diff(project, self.projects_api.get_project, obfuscate=True)
                project_diff["/projects/:id/variables"] = self.generate_diff(project, self.variables_api.get_variables, obfuscate=True, var_type="project")
                project_diff["/projects/:id/members"] = self.generate_diff(project, self.projects_api.get_members)
                project_diff["/projects/:id/environments"] = self.generate_diff(project, self.environments_api.get_all_environments)
                diff_report[project["path_with_namespace"]] = project_diff
                diff_report[project["path_with_namespace"]]["overall_accuracy"] = self.calculate_overall_accuracy(diff_report[project["path_with_namespace"]])
            else:
                diff_report[project["path_with_namespace"]] = {
                    "error": "project missing",
                    "overall_accuracy": {
                        "accuracy": 0,
                        "result": "failure"
                    }
                }

        diff_report["project_migration_results"] = self.calculate_overall_stage_accuracy(diff_report)

        return diff_report

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
                destination_project_data = self.generate_empty_data(source_project_data)
            
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
            instance_data = self.ignore_keys(list(instance_data))
        else:
            instance_data = self.ignore_keys(instance_data.json())
        return instance_data
