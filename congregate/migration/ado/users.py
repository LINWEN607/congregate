from gitlab_ps_utils.misc_utils import strip_netloc, is_error_message_present

from congregate.migration.ado.api.users import UsersApi
# from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.migration.ado.base import AzureDevOpsWrapper

from congregate.helpers.congregate_mdbc import CongregateMongoConnector


class UsersClient(AzureDevOpsWrapper):
    def __init__(self):
        self.users_api = UsersApi()
        super().__init__()

    def retrieve_user_info(self, processes=None):
        """
        List and transform all Azure DevOps user to GitLab user metadata
        """
        for user in self.users_api.get_all_users():
            self.handle_retrieving_users(user)

        # self.multi.start_multi_process_stream_with_args(
        #     self.handle_retrieving_users, self.users_api.get_all_users(), processes=processes, nestable=True)

    def handle_retrieving_users(self, user, mongo=None):
        error, resp = is_error_message_present(user)
        if resp and not error:
            # mongo should be set to None unless this function is being used in a
            # unit test
            if not mongo:
                mongo = CongregateMongoConnector()
            if formatted_user := self.format_user(user):
                mongo.insert_data(
                    f"users-{strip_netloc(self.config.source_host)}",
                    formatted_user)
            mongo.close_connection()
        else:
            self.log.error(resp)
