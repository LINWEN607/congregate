from types import GeneratorType
from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.variables import VariablesApi
from congregate.helpers.misc_utils import rewrite_list_into_dict

class ProjectDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated users
    '''
    def __init__(self, results_file, staged=False):
        super(ProjectDiffClient, self).__init__()
        self.projects_api = ProjectsApi()
        self.variables_api = VariablesApi()
        self.results = self.load_json_data(results_file)
        self.keys_to_ignore = [
            "id"
        ]

        if staged:
            self.source_data = self.load_json_data("%s/data/stage.json" % self.app_path)
        else:
            self.source_data = self.load_json_data("%s/data/project_json.json" % self.app_path)

    def generate_project_diff_report(self):
        diff_report = {}
        self.log.info("Generating Project Diff Report")
        
        for project in self.source_data:
            project_diff = {}
            project_diff["/projects/:id"] = self.generate_diff(project, self.projects_api.get_project)
            project_diff["/projects/:id/variables"] = self.generate_diff(project, self.variables_api.get_variables, obfuscate=True, var_type="project")
            project_diff["/projects/:id/members"] = self.generate_diff(project, self.projects_api.get_members)
            diff_report[project["full_path"]] = project_diff

        return diff_report

    def generate_diff(self, project, endpoint, critical_key=None, obfuscate=False, **kwargs):
        source_project_data = self.generate_cleaned_instance_data(
            endpoint(project["id"], self.config.source_host, self.config.source_token, **kwargs))
        if self.results.get(project["full_path"]) is not None:
            destination_project_id = self.results[project["full_path"]]["id"]
            destination_project_data = self.generate_cleaned_instance_data(
                endpoint(destination_project_id, self.config.destination_host, self.config.destination_token, **kwargs))
        elif self.results.get(project["path"]) is not None:
            destination_project_id = self.results[project["path"]]["id"]
            destination_project_data = self.generate_cleaned_instance_data(
                endpoint(destination_project_id, self.config.destination_host, self.config.destination_token, **kwargs))
        else:
            if isinstance(source_project_data, list):
                destination_project_data = []
            elif isinstance(source_project_data, dict):
                destination_project_data = {
                    "error": "project missing"
                }
        if source_project_data == {} and destination_project_data == {}:
            return self.empty_diff()
        elif source_project_data == [] and destination_project_data == []:
            return self.empty_diff()
            
        return self.diff(source_project_data, destination_project_data, critical_key=critical_key, obfuscate=obfuscate)

    def generate_cleaned_instance_data(self, instance_data):
        if isinstance(instance_data, GeneratorType):
            instance_data = self.ignore_keys(list(instance_data))
        else:
            instance_data = self.ignore_keys(instance_data.json())
        return instance_data
