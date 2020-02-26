from types import GeneratorType
from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.variables import VariablesClient
from congregate.helpers.misc_utils import rewrite_json_list_into_dict

class GroupDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated groups
    '''
    def __init__(self, results_file, staged=False):
        super(GroupDiffClient, self).__init__()
        self.groups_api = GroupsApi()
        self.variables_api = VariablesClient()
        self.results = rewrite_json_list_into_dict(self.load_json_data(results_file))
        self.keys_to_ignore = [
            "id",
            "projects",
            "runners_token",
            "web_url"
        ]

        if staged:
            self.source_data = self.load_json_data("%s/data/staged_groups.json" % self.app_path)
        else:
            self.source_data = self.load_json_data("%s/data/groups.json" % self.app_path)

    def generate_group_diff_report(self):
        diff_report = {}
        self.log.info("Generating Group Diff Report")
        
        for group in self.source_data:
            if self.results.get(group["full_path"]) is not None or self.results.get(group["path"]) is not None:
                group_diff = {}
                group_diff["/groups/:id"] = self.generate_diff(group, self.groups_api.get_group, critical_key="full_path")
                group_diff["/groups/:id/variables"] = self.generate_diff(group, self.variables_api.get_variables, obfuscate=True, var_type="group")
                group_diff["/groups/:id/members"] = self.generate_diff(group, self.groups_api.get_all_group_members)
                diff_report[group["full_path"]] = group_diff
                diff_report[group["full_path"]]["overall_accuracy"] = self.calculate_overall_accuracy(diff_report[group["full_path"]])
            else:
                diff_report[group["full_path"]] = {
                    "error": "group missing",
                    "overall_accuracy": {
                        "accuracy": 0,
                        "result": "failure"
                    }
                }

        diff_report["group_migration_results"] = self.calculate_overall_stage_accuracy(diff_report)

        return diff_report

    def generate_diff(self, group, endpoint, critical_key=None, obfuscate=False, **kwargs):
        source_group_data = self.generate_cleaned_instance_data(
            endpoint(group["id"], self.config.source_host, self.config.source_token, **kwargs))
        if self.results.get(group["full_path"]) is not None:
            destination_group_id = self.results[group["full_path"]]["id"]
            destination_group_data = self.generate_cleaned_instance_data(
                endpoint(destination_group_id, self.config.destination_host, self.config.destination_token, **kwargs))
        elif self.results.get(group["path"]) is not None:
            destination_group_id = self.results[group["path"]]["id"]
            destination_group_data = self.generate_cleaned_instance_data(
                endpoint(destination_group_id, self.config.destination_host, self.config.destination_token, **kwargs))
        else:
            if isinstance(source_group_data, list):
                destination_group_data = []
            elif isinstance(source_group_data, dict):
                destination_group_data = {
                    "error": "group missing"
                }
        if source_group_data == {} and destination_group_data == {}:
            return self.empty_diff()
        elif source_group_data == [] and destination_group_data == []:
            return self.empty_diff()
            
        return self.diff(source_group_data, destination_group_data, critical_key=critical_key, obfuscate=obfuscate)

    def generate_cleaned_instance_data(self, instance_data):
        if isinstance(instance_data, GeneratorType):
            instance_data = self.ignore_keys(list(instance_data))
        else:
            instance_data = self.ignore_keys(instance_data.json())
        return instance_data
