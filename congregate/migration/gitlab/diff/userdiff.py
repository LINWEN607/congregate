from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.helpers.misc_utils import rewrite_list_into_dict, get_rollback_log


class UserDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated users
    '''

    def __init__(self, results_path, staged=False):
        super(UserDiffClient, self).__init__()
        self.users_api = UsersApi()
        self.results = self.load_json_data(
            "{0}{1}".format(self.app_path, results_path))
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
            "id"
        ]
        if staged:
            self.source_data = rewrite_list_into_dict(self.load_json_data(
                "%s/data/staged_users.json" % self.app_path), "email")
        else:
            self.source_data = rewrite_list_into_dict(
                self.load_json_data("%s/data/users.json" % self.app_path), "email")

    def generate_diff_report(self, rollback=False):
        diff_report = {}
        self.log.info("{}Generating User Diff Report".format(
            get_rollback_log(rollback)))

        for user in self.results:
            destination_user_data = self.ignore_keys(self.users_api.get_user(
                user["id"], self.config.destination_host, self.config.destination_token).json())
            source_user_data = self.ignore_keys(self.users_api.get_user(
                self.source_data[user["email"]]["id"], self.config.source_host, self.config.source_token).json())
            diff_report[user["email"]] = (
                self.diff(source_user_data, destination_user_data, user["email"]))

        diff_report["user_migration_results"] = self.calculate_overall_accuracy(
            diff_report)
        return diff_report
