from congregate.helpers.base_class import BaseClass
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.api.users import UsersApi
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.misc_utils import strip_netloc, is_error_message_present


class UsersClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.users_api = UsersApi()
        super().__init__()
        self.users_to_ignore = self.config.users_to_ignore

    def connect_to_mongo(self):
        return MongoConnector()

    def retrieve_user_info(self, processes=None):
        """
        List and transform all Bitbucket Server user to GitLab user metadata
        """
        self.multi.start_multi_process_stream_with_args(
            self.handle_retrieving_users, self.users_api.get_all_users(), processes=processes, nestable=True)

    def handle_retrieving_users(self, user, mongo=None):
        error, resp = is_error_message_present(user)
        if resp and not error:
            # mongo should be set to None unless this function is being used in a
            # unit test
            if not mongo:
                mongo = self.connect_to_mongo()
            if formatted_user := self.format_user(user):
                mongo.insert_data(
                    f"users-{strip_netloc(self.config.source_host)}", formatted_user)
            mongo.close_connection()
        else:
            self.log.error(resp)

    def format_user(self, user):
        if self.is_user_needed(user) and user.get("emailAddress"):
            return {
                "id": user["id"],
                "username": user["slug"],
                "name": user["displayName"],
                "email": user["emailAddress"].lower(),
                "state": "active"
            }
        self.log.warning(
            f"User {user['slug']} is either not needed or missing an email address. Skipping")

    def is_user_needed(self, user):
        if user['id'] == 1 or user["slug"].lower() in self.users_to_ignore:
            return False
        return True

    def format_users(self, users):
        data = []
        for user in users:
            formatted_user = self.format_user(user)
            if not formatted_user:
                continue
            if user.get("permission"):
                formatted_user["access_level"] = user["permission"]
            data.append(formatted_user)
        return data
