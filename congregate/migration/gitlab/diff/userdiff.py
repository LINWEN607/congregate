from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.helpers.misc_utils import rewrite_list_into_dict

class UserDiffClient(BaseDiffClient):
    def __init__(self, results_file, staged=False):
        self.users_api = UsersApi()
        self.results = self.load_json_data(results_file)
        if staged:
            self.source_data = rewrite_list_into_dict(self.load_json_data("%s/data/staged_users.json" % self.app_path), "email")
        else:
            self.source_data = rewrite_list_into_dict(self.load_json_data("%s/data/users.json" % self.app_path), "email")
        super(UserDiffClient, self).__init__()

    def generate_report(self):
        diff_report = []
        self.log.info("Generating User Diff Report")
        for user in self.results:
            destination_user_data = self.users_api.get_user(user["id"], self.config.source_host, self.config.source_token).json()
            source_user_data = self.source_data[user["email"]]
            diff_report.append(self.diff(source_user_data, destination_user_data, user["email"]))

        return diff_report
    

    