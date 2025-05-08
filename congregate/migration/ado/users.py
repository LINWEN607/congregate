from gitlab_ps_utils.misc_utils import strip_netloc
from celery import shared_task
from congregate.helpers.congregate_mdbc import mongo_connection

from congregate.migration.ado.api.users import UsersApi
from congregate.migration.ado.base import AzureDevOpsWrapper
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector


class UsersClient(BaseClass):
    def __init__(self):
        self.base_api = AzureDevOpsWrapper()
        self.users_api = UsersApi()
        super().__init__()

    def retrieve_user_info(self, processes=None):
        """
        List and transform all Azure DevOps user to GitLab user metadata
        """
        users = self.users_api.get_all_users()
        if self.config.direct_transfer:
            self.log.info("Direct transfer enabled - queuing ADO users via Celery")
            for user in users:
                handle_retrieving_ado_users_task.delay(user)
        else:
            self.log.info("Direct transfer disabled - using multiprocessing for ADO users")
            self.multi.start_multi_process_stream_with_args(
                self.handle_retrieving_user, users, processes=processes)

    def handle_retrieving_user(self, user, mongo=None):
        if not mongo:
            mongo = CongregateMongoConnector()
        if user:
            mongo.insert_data(
                f"users-{strip_netloc(self.config.source_host)}",
                self.base_api.format_user(user))
        else:
            self.log.error("Failed to retrieve user information")
        mongo.close_connection()


@shared_task(name='retrieve-ado-users')
@mongo_connection
def handle_retrieving_ado_users_task(user, mongo=None):
    user_client = UsersClient()
    user_client.log.info("Handling ADO user via Celery task")
    if user:
        mongo.insert_data(
            f"users-{strip_netloc(user_client.config.source_host)}",
            user_client.base_api.format_user(user)
        )
    else:
        user_client.log.error(f"Failed to process ADO user data. Was provided [{user}]")
    mongo.close_connection()
