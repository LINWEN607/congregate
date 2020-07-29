import json
import requests
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes
from congregate.migration.github.api.users import UsersApi


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
        for user in users:
            single_user=self.users_api.get_user(user["login"]).json()
            data.append({
                   "id": user["id"],
                    "username": user["login"],
                    "name": single_user["name"],
                    # "email": single_user["email"],
                    "web_url": user["html_url"],
                    "avatar_url": single_user["avatar_url"],
                    #"state": "blocked" if single_user["suspended_at"] else "active",
                    #"two_factor_enabled": single_user["two_factor_authentication"] 
            })
        return data