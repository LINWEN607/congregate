from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.migration.github.api.users import UsersApi
from congregate.helpers.misc_utils import safe_json_response, is_error_message_present


class UsersClient(BaseClass):
    def __init__(self):
        super(UsersClient, self).__init__()
        self.users_api = UsersApi(self.config.source_host,
                                  self.config.source_token)
        self.mongo = self.connect_to_mongo()

    def connect_to_mongo(self):
        return MongoConnector()

    def retrieve_user_info(self):
        """
        List and transform all GitHub user to GitLab user metadata
        """
        for user in self.users_api.get_all_users():
            formatted_user = self.format_user(user)
            self.mongo.insert_data("users", formatted_user)

    def format_users(self, users):
        data = []
        for user in users:
            single_user = safe_json_response(
                self.users_api.get_user(user["login"]))
            if not single_user or is_error_message_present(single_user):
                self.log.error("Failed to get JSON for user {} ({})".format(
                    user["login"], single_user))
            else:
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

    def format_user(self, single_user):
        return {
            "id": single_user["id"],
            "username": single_user["login"],
            "name": single_user.get("name", None),
            "email": single_user.get("email", None),
            "avatar_url": "" if self.config.source_host in single_user["avatar_url"] else single_user["avatar_url"],
            "state": "blocked" if single_user.get("suspended_at", None) else "active",
            "is_admin": single_user["site_admin"]
        }
