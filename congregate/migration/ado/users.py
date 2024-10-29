from gitlab_ps_utils.misc_utils import strip_netloc

from congregate.migration.ado.api.users import UsersApi
from congregate.migration.ado.base import AzureDevOpsWrapper
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import mongo_connection


class UsersClient(BaseClass):
    def __init__(self):
        self.base_api = AzureDevOpsWrapper()
        self.users_api = UsersApi()
        super().__init__()

    def retrieve_user_info(self, processes=None):
        """
        List and transform all Azure DevOps user to GitLab user metadata
        """
        # self.multi.start_multi_process_stream_with_args(
        #     self.handle_retrieving_user, self.users_api.get_all_users(), processes=processes, nestable=True)
        for user in self.users_api.get_all_users():
            self.handle_retrieving_user(user)

    @mongo_connection
    def handle_retrieving_user(self, user, mongo=None):
        if user:
            mongo.insert_data(
                f"users-{strip_netloc(self.config.source_host)}",
                self.base_api.format_user(user))
        else:
            self.log.error("Failed to retrieve user information")
