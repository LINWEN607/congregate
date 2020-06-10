from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.migration.gitlab.groups import GroupsClient
from congregate.helpers.misc_utils import rewrite_json_list_into_dict, get_rollback_log
from congregate.helpers.migrate_utils import get_full_path_with_parent_namespace, is_top_level_group
from congregate.helpers.processes import handle_multi_process_write_to_file_and_return_results


class GroupDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated groups
    '''

    def __init__(self, results_path, staged=False, rollback=False, processes=None):
        super(GroupDiffClient, self).__init__()
        self.groups_api = GroupsApi()
        self.issues_api = IssuesApi()
        self.mr_api = MergeRequestsApi()
        self.groups = GroupsClient()
        self.results = rewrite_json_list_into_dict(
            self.load_json_data("{0}{1}".format(self.app_path, results_path)))
        self.rollback = rollback
        self.processes = processes
        self.keys_to_ignore = [
            "id",
            "projects",
            "runners_token",
            "web_url",
            "created_at",
            "marked_for_deletion_on"
        ]
        if staged:
            self.source_data = self.load_json_data(
                "%s/data/staged_groups.json" % self.app_path)
        else:
            self.source_data = self.load_json_data(
                "%s/data/groups.json" % self.app_path)
        # Keep only top level groups
        self.source_data = [
            d for d in self.source_data if is_top_level_group(d)]

    def generate_diff_report(self):
        diff_report = {}
        self.log.info("{}Generating Group Diff Report".format(
            get_rollback_log(self.rollback)))
        results = handle_multi_process_write_to_file_and_return_results(
            self.generate_single_diff_report, self.return_only_accuracies, self.source_data, "%s/data/group_diff.json" % self.app_path, processes=self.processes)

        for result in results:
            diff_report.update(result)

        diff_report["group_migration_results"] = self.calculate_overall_stage_accuracy(
            diff_report)

        return diff_report

    def generate_single_diff_report(self, group):
        diff_report = {}
        group_path = get_full_path_with_parent_namespace(group["full_path"])
        if isinstance(self.results.get(group_path), int) and self.results.get(group_path):
            return {
                group_path: {
                    "info": "group already migrated",
                    "overall_accuracy": {
                        "accuracy": 1,
                        "result": "uknown"
                    }
                }
            }
        elif self.results.get(group_path) and self.asset_exists(self.groups_api.get_group, self.results[group_path].get("id")):
            group_diff = self.handle_endpoints(group)
            diff_report[group_path] = group_diff
            try:
                diff_report[group_path]["overall_accuracy"] = self.calculate_overall_accuracy(
                    diff_report[group_path])
                return diff_report
            except Exception:
                self.log.info("Failed to generate diff for %s" % group_path)
        return {
            group_path: {
                "error": "group missing",
                "overall_accuracy": {
                    "accuracy": 0,
                    "result": "failure"
                }
            }
        }

    def handle_endpoints(self, group):
        group_diff = {}
        group_diff["/groups/:id"] = self.generate_group_diff(
            group, self.groups_api.get_group, critical_key="full_path")

        if not self.rollback:
            group_diff["/groups/:id/variables"] = self.generate_group_diff(
                group, self.groups_api.get_all_group_variables, obfuscate=True)
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
            group_diff["/groups/:id/registry/repositories"] = self.generate_group_diff(
                group, self.groups_api.get_all_group_registry_repositories)
            group_diff["/groups/:id/badges"] = self.generate_group_diff(
                group, self.groups_api.get_all_group_badges)
        return group_diff

    def generate_group_diff(self, group, endpoint, **kwargs):
        return self.generate_diff(group, "full_path", endpoint, parent_group=self.config.dstn_parent_group_path, **kwargs)
