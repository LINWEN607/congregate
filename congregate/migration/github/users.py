import json
from congregate.helpers.base_class import BaseClass
from congregate.migration.github.api.users import UsersApi
from congregate.helpers.misc_utils import remove_dupes, safe_json_response

class UsersClient(BaseClass):
    def __init__(self):
        super(UsersClient, self).__init__()
        self.users_api = UsersApi(self.config.source_host,
                                self.config.source_token)

    def retrieve_user_info(self):
        users = self.users_api.get_all_users()
        # List and reformat all GitHub user to GitLab metadata
        data = remove_dupes(self.format_users(users))
        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(data, f, indent=4)

        return data

    def format_users(self, users):
        data = []
        for single_user in users:
            user= safe_json_response(self.users_api.get_user(single_user["login"]))
            data.append({
                   "id": single_user["id"],
                    "username": single_user["login"],
                    #"name": user["name"],
                    # "email": user["email"],
                    "state": "blocked" if user["suspended_at"] else "active",
            })
            if user.get("name", None):
                data[-1]["name"] = user["name"] 
            if user.get("email", None):
                data[-1]["email"] = user["email"] 
            # When formatting project and repo users
            if single_user.get("permission", None):
                data[-1]["access_level"] = user["permission"]
        return data