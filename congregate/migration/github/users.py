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
        """
        List and transform all GitHub user to GitLab user metadata
        """
        users = self.users_api.get_all_users()
        data = remove_dupes(self.format_users(users))
        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(data, f, indent=4)
        return data

    def format_users(self, users):
        data = []
        for user in users:
            single_user = safe_json_response(
                self.users_api.get_user(user["login"]))
            data.append({
                "id": single_user["id"],
                "username": single_user["login"],
                "name": single_user.get("name", None),
                "email": single_user.get("email", None),
                "avatar_url": "" if self.config.source_host in single_user["avatar_url"] else single_user["avatar_url"],
                "state": "blocked" if single_user["suspended_at"] else "active",
                "is_admin": single_user["site_admin"]
            })
            # When formatting org, team and repo users
            if user.get("permissions", None):
                data[-1]["access_level"] = user["permissions"]
        return data
