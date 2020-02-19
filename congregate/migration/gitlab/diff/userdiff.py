from congregate.migration.gitlab.diff.basediff import BaseDiffClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.helpers.misc_utils import rewrite_list_into_dict

class UserDiffClient(BaseDiffClient):
    '''
        Extension of BaseDiffClient focused on finding the differences between migrated users
    '''
    def __init__(self, results_file, staged=False):
        super(UserDiffClient, self).__init__()
        self.users_api = UsersApi()
        self.results = self.load_json_data(results_file)
        self.keys_to_ignore = [
            "web_url"
            "last_sign_in_at",
            "last_activity_at",
            "current_sign_in_at",
            "created_at",
            "confirmed_at",
            "last_activity_on",
            "id"
        ]
        if staged:
            self.source_data = rewrite_list_into_dict(self.load_json_data("%s/data/staged_users.json" % self.app_path), "email")
        else:
            self.source_data = rewrite_list_into_dict(self.load_json_data("%s/data/users.json" % self.app_path), "email")

    def generate_report(self):
        diff_report = []
        self.log.info("Generating User Diff Report")
        
        for user in self.results:
            destination_user_data = self.ignore_keys(self.users_api.get_user(user["id"], self.config.destination_host, self.config.destination_token).json())
            source_user_data = self.ignore_keys(self.source_data[user["email"]])
            diff_report.append(self.diff(source_user_data, destination_user_data, user["email"]))

        return diff_report
    
