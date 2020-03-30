from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.migration.gitlab.groups import GroupsClient
from congregate.helpers.misc_utils import rewrite_json_list_into_dict, get_rollback_log
from congregate.helpers.threads import handle_multi_thread_write_to_file_and_return_results


class GroupDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated groups
    '''

    def __init__(self, results_path, staged=False):
        super(GroupDiffClient, self).__init__()
        self.groups_api = GroupsApi()
        self.issues_api = IssuesApi()
        self.mr_api = MergeRequestsApi()
        self.groups = GroupsClient()
        self.results = rewrite_json_list_into_dict(
            self.load_json_data("{0}{1}".format(self.app_path, results_path)))
        self.keys_to_ignore = [
            "id",
            "projects",
            "runners_token",
            "web_url",
            "created_at"
        ]

        if staged:
            self.source_data = self.load_json_data(
                "%s/data/staged_groups.json" % self.app_path)
        else:
            self.source_data = self.load_json_data(
                "%s/data/groups.json" % self.app_path)

    def generate_diff_report(self, rollback=False):
        diff_report = {}
        self.log.info("{}Generating Group Diff Report".format(
            get_rollback_log(rollback)))

        results = handle_multi_thread_write_to_file_and_return_results(
            self.generate_single_diff_report, self.return_only_accuracies, self.source_data, "%s/data/group_diff.json" % self.app_path)

        for result in results:
            diff_report.update(result)

        diff_report["group_migration_results"] = self.calculate_overall_stage_accuracy(
            diff_report)

        return diff_report

    def generate_single_diff_report(self, group):
        diff_report = {}
        group_path = "%s/%s" % (self.config.parent_group_path,
                                group["full_path"]) if self.config.parent_group_path else group["full_path"]
        if self.results.get(group_path) is not None or self.results.get(group["path"]) is not None:
            group_diff = self.handle_endpoints(group)
            diff_report[group_path] = group_diff
            diff_report[group_path]["overall_accuracy"] = self.calculate_overall_accuracy(
                diff_report[group_path])
        else:
            found_group = self.groups_api.get_group_by_full_path(
                group_path, self.config.destination_host, self.config.destination_token)
            if found_group.status_code == 200:
                self.results[group_path] = found_group.json()
                group_diff = self.handle_endpoints(group)
                diff_report[group_path] = group_diff
                diff_report[group_path]["overall_accuracy"] = self.calculate_overall_accuracy(
                    diff_report[group_path])
            else:
                diff_report[group_path] = {
                    "error": "group missing",
                    "overall_accuracy": {
                        "accuracy": 0,
                        "result": "failure"
                    }
                }
        return diff_report

    def handle_endpoints(self, group):
        group_diff = {}
        parent_group = self.config.parent_group_path
        group_diff["/groups/:id"] = self.generate_group_diff(
            group, self.groups_api.get_group, critical_key="full_path", parent_group=parent_group)
        group_diff["/groups/:id/variables"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_variables, obfuscate=True, var_type="group")
        group_diff["/groups/:id/members"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_members)
        group_diff["/groups/:id/boards"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_issue_boards)
        group_diff["/groups/:id/labels"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_labels)
        group_diff["/groups/:id/milestones"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_milestones)
        group_diff["/groups/:id/hooks"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_hooks)
        group_diff["/groups/:id/projects"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_projects)
        group_diff["/groups/:id/subgroups"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_subgroups)
        group_diff["/groups/:id/epics"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_epics)
        group_diff["/groups/:id/custom_attributes"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_custom_attributes)
        group_diff["/groups/:id/members/all"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_members_incl_inherited)
        group_diff["/groups/:id/registry/repositories"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_registry_repositories)
        group_diff["/groups/:id/badges"] = self.generate_group_diff(
            group, self.groups_api.get_all_group_badges)
        group_diff["/groups/:id/merge_requests"] = self.generate_group_diff(
            group, self.mr_api.get_all_group_merge_requests)
        return group_diff

    def generate_group_diff(self, group, endpoint, **kwargs):
        return self.generate_diff(group, "full_path", endpoint)
