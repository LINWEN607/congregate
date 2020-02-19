from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.helpers.misc_utils import rewrite_list_into_dict

class GroupDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated users
    '''
    def __init__(self, results_file, staged=False):
        super(GroupDiffClient, self).__init__()
        self.groups_api = GroupsApi()
        self.results = rewrite_list_into_dict(self.load_json_data(results_file), "full_path")
        self.keys_to_ignore = [
            "id",
            "projects",
            "runners_token",
            "web_url"
        ]
        # if staged:
        #     self.source_data = rewrite_list_into_dict(self.load_json_data("%s/data/staged_groups.json" % self.app_path), "full_path")
        # else:
        #     self.source_data = rewrite_list_into_dict(self.load_json_data("%s/data/groups.json" % self.app_path), "full_path")

        if staged:
            self.source_data = self.load_json_data("%s/data/staged_groups.json" % self.app_path)
        else:
            self.source_data = self.load_json_data("%s/data/groups.json" % self.app_path)

    def generate_base_diff(self):
        diff_report = {}
        self.log.info("Generating Base Group Diff Report")
        
        for group in self.source_data:
            source_group_data = self.ignore_keys(self.groups_api.get_group(group["id"], self.config.source_host, self.config.source_token).json())
            if self.results.get(group["full_path"]) is not None:
                destination_group_id = self.results[group["full_path"]]["id"]
                destination_group_data = self.ignore_keys(self.groups_api.get_group(destination_group_id, self.config.destination_host, self.config.destination_token).json())
            elif self.results.get(group["path"]) is not None:
                destination_group_id = self.results[group["path"]]["id"]
                destination_group_data = self.ignore_keys(self.groups_api.get_group(destination_group_id, self.config.destination_host, self.config.destination_token).json())
            else:
                destination_group_data = {
                    "error": "group missing"
                }
            diff_report[group["full_path"]] = self.diff(source_group_data, destination_group_data, critical_key="full_path")

        return diff_report
    
    def ignore_keys(self, data):
        for key in self.keys_to_ignore:
            if key in data:
                data.pop(key)
        return data

    