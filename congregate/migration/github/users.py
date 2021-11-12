from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.migration.github.api.users import UsersApi
from congregate.migration.github.api.orgs import OrgsApi
from congregate.migration.github.meta.github_browser import GitHubBrowser
from congregate.helpers.misc_utils import safe_json_response, is_error_message_present, strip_netloc
from congregate.helpers.utils import is_github_dot_com


class UsersClient(BaseClass):
    def __init__(self, host, token, username=None, password=None):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.users_api = UsersApi(host, token)
        self.orgs_api = OrgsApi(host, token)

    def connect_to_mongo(self):
        return MongoConnector()

    def establish_browser_connection(self):
        if self.username and self.password:
            return GitHubBrowser(self.host, self.username, self.password)
        else:
            self.log.warning(
                "Username/password not set in UseClient initialization. Skipping github browser connection")

    def retrieve_user_info(self, processes=None):
        """
        List and transform all GitHub user to GitLab user metadata
        """
        if self.config.src_parent_org or (is_github_dot_com(
                self.config.source_host) and self.config.src_parent_org):
            users = []
            for m in self.orgs_api.get_all_org_members(
                    self.config.src_parent_org):
                users.append(safe_json_response(
                    self.users_api.get_user(m["login"])))
        else:
            users = self.users_api.get_all_users()
        self.multi.start_multi_process_stream_with_args(
            self.handle_retrieving_users, users, self.establish_browser_connection(), processes=processes, nestable=True)

    def handle_retrieving_users(self, browser, user, mongo=None):
        # mongo should be set to None unless this function is being used in a
        # unit test
        if not mongo:
            mongo = self.connect_to_mongo()
        single_user = safe_json_response(
            self.users_api.get_user(user["login"]))
        error, single_user = is_error_message_present(single_user)
        if error or not single_user:
            self.log.error("Failed to get JSON for user {} ({})".format(
                user["login"], single_user))
        else:
            if single_user.get("type") != "Organization":
                formatted_user = self.format_user(single_user, browser, mongo)
                mongo.insert_data(
                    f"users-{strip_netloc(self.host)}", formatted_user)
        mongo.close_connection()

    def format_users(self, users, mongo):
        data = []
        for user in users:
            single_user = safe_json_response(
                self.users_api.get_user(user["login"]))
            error, single_user = is_error_message_present(single_user)
            if error or not single_user:
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
            "name": single_user["name"] or single_user["login"],
            "email": self.get_email_address(single_user, github_browser, mongo),
            "avatar_url": single_user.get("avatar_url", ""),
            "state": "blocked" if single_user.get("suspended_at", None) else "active",
            "is_admin": single_user["site_admin"]
        }

    def get_email_address(self, single_user, github_browser, mongo):
        if email := single_user.get("email", None):
            return email
        elif email := mongo.find_user_email(single_user["login"]):
            return email
        elif github_browser:
            self.log.warning(
                f"User email not found. Attempting to scrape for username {single_user['login']}")
            return github_browser.scrape_user_email(single_user["login"])
