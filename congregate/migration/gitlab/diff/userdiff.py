from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.helpers.misc_utils import rewrite_json_list_into_dict, get_rollback_log, is_error_message_present
from congregate.helpers.threads import handle_multi_thread_write_to_file_and_return_results


class UserDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated users
    '''

    def __init__(self, results_path, staged=False, rollback=False):
        super(UserDiffClient, self).__init__()
        self.users_api = UsersApi()
        self.results = self.load_json_data(
            "{0}{1}".format(self.app_path, results_path))
        self.rollback = rollback
        self.keys_to_ignore = [
            "web_url",
            "last_sign_in_at",
            "last_activity_at",
            "current_sign_in_at",
            "created_at",
            "confirmed_at",
            "last_activity_on",
            "current_sign_in_ip",
            "last_sign_in_ip",
            "source_id",
            "id",
            "author_id",
            "project_id",
            "target_id"
        ]
        if staged:
            self.source_data = self.load_json_data(
                "%s/data/staged_users.json" % self.app_path)
        else:
            self.source_data = self.load_json_data(
                "%s/data/users.json" % self.app_path)

    def generate_diff_report(self):
        diff_report = {}
        self.log.info("{}Generating User Diff Report".format(
            get_rollback_log(self.rollback)))

        results = handle_multi_thread_write_to_file_and_return_results(
            self.generate_single_diff_report, self.return_only_accuracies, self.source_data, "%s/data/user_diff.json" % self.app_path)

        for result in results:
            diff_report.update(result)

        diff_report["user_migration_results"] = self.calculate_overall_stage_accuracy(
            diff_report)

        return diff_report

    def generate_single_diff_report(self, user):
        diff_report = {}
        user_email = user["email"]
        if self.results.get(user_email):
            if self.asset_exists(self.users_api.get_user, self.results[user_email].get("id")):
                user_diff = self.handle_endpoints(user)
                diff_report[user_email] = user_diff
                diff_report[user_email]["overall_accuracy"] = self.calculate_overall_accuracy(
                    diff_report[user_email])
                return diff_report
        return {
            user_email: {
                "error": "user missing",
                "overall_accuracy": {
                    "accuracy": 0,
                    "result": "failure"
                }
            }
        }

    def handle_endpoints(self, user):
        user_diff = {}
        # General endpoint
        user_diff["/users/:id"] = self.generate_user_diff(
            user, self.users_api.get_user, obfuscate=True)
        if not self.rollback:
            user_diff["/users/:id/projects"] = self.generate_user_diff(
                user, self.users_api.get_all_user_projects)
            user_diff["/users/:id/emails"] = self.generate_user_diff(
                user, self.users_api.get_all_user_emails)
            user_diff["/users/:id/memberships"] = self.generate_user_diff(
                user, self.users_api.get_all_user_memberships)
            user_diff["/users/:id/events"] = self.generate_user_diff(
                user, self.users_api.get_all_user_contribution_events)
            user_diff["/users/:id/custom_attributes"] = self.generate_user_diff(
                user, self.users_api.get_all_user_custom_attributes)

        return user_diff

    def generate_user_diff(self, user, endpoint, **kwargs):
        return self.generate_diff(user, "email", endpoint, **kwargs)