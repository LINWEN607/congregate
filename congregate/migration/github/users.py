from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.processes import start_multi_process_stream
from congregate.migration.github.api.users import UsersApi
from congregate.helpers.misc_utils import safe_json_response, is_error_message_present


class UsersClient(BaseClass):
    def __init__(self):
        super(UsersClient, self).__init__()
        self.users_api = UsersApi(self.config.source_host,
                                  self.config.source_token)

    def connect_to_mongo(self):
        return MongoConnector()

    def retrieve_user_info(self, processes=None):
        """
        List and transform all GitHub user to GitLab user metadata
        """
        start_multi_process_stream(self.handle_retrieving_users, self.users_api.get_all_users(), processes=processes)
    
    def handle_retrieving_users(self, user, mongo=None):
        # mongo should be set to None unless this function is being used in a unit test
        if not mongo:
            mongo = self.connect_to_mongo()
        formatted_user = self.format_user(user)
        mongo.insert_data("users", formatted_user)
        mongo.close_connection()

    def format_users(self, users):
        data = []
        for user in users:
            single_user = safe_json_response(
                self.users_api.get_user(user["login"]))
            if not single_user or is_error_message_present(single_user):
                self.log.error("Failed to get JSON for user {} ({})".format(
                    user["login"], single_user))
            else:
                data.append(self.format_user(single_user))
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
