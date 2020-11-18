from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.processes import start_multi_process_stream_with_args
from congregate.migration.github.api.users import UsersApi
from congregate.migration.github.meta.github_browser import GitHubBrowser
from congregate.helpers.misc_utils import safe_json_response, is_error_message_present


class UsersClient(BaseClass):
    def __init__(self):
        super(UsersClient, self).__init__()
        self.users_api = UsersApi(self.config.source_host,
                                  self.config.source_token)

    def connect_to_mongo(self):
        return MongoConnector()
    
    def establish_browser_connection(self):
        return GitHubBrowser(self.config.source_host, self.config.source_username, self.config.source_password)

    def retrieve_user_info(self, processes=None):
        """
        List and transform all GitHub user to GitLab user metadata
        """
        start_multi_process_stream_with_args(self.handle_retrieving_users, self.users_api.get_all_users(), self.establish_browser_connection(), processes=processes)
    
    def handle_retrieving_users(self, browser, user, mongo=None):
        # mongo should be set to None unless this function is being used in a unit test
        if not mongo:
            mongo = self.connect_to_mongo()
        single_user = safe_json_response(
            self.users_api.get_user(user["login"]))
        if not single_user or is_error_message_present(single_user):
            self.log.error("Failed to get JSON for user {} ({})".format(
                user["login"], single_user))
        else:
            if single_user.get("type") != "Organization":
                formatted_user = self.format_user(single_user, browser, mongo)
                mongo.insert_data("users", formatted_user)
        mongo.close_connection()

    def format_users(self, users, mongo):
        data = []
        for user in users:
            single_user = safe_json_response(
                self.users_api.get_user(user["login"]))
            if not single_user or is_error_message_present(single_user):
                self.log.error("Failed to get JSON for user {} ({})".format(
                    user["login"], single_user))
            else:
                data.append(self.format_user(single_user, None, mongo))
                # When formatting org, team and repo users
                if user.get("permissions", None):
                    data[-1]["access_level"] = user["permissions"]
        return data

    def format_user(self, single_user, github_browser, mongo):
        return {
            "id": single_user["id"],
            "username": single_user["login"],
            "name": single_user.get("name", None),
            "email": self.get_email_address(single_user, github_browser, mongo),
            "avatar_url": "" if self.config.source_host in single_user["avatar_url"] else single_user["avatar_url"],
            "state": "blocked" if single_user.get("suspended_at", None) else "active",
            "is_admin": single_user["site_admin"]
        }
    
    def get_email_address(self, single_user, github_browser, mongo):
        if email := single_user.get("email", None):
            return email
        elif email := mongo.find_user_email(single_user["email"]):
            return email
        elif github_browser:
            self.log.warning(f"User email not found. Attempting to scrape for username {single_user['login']}")
            return github_browser.scrape_user_email(single_user["login"])
