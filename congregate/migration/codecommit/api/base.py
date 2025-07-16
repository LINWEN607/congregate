import boto3

from botocore.config import Config
from congregate.helpers.base_class import BaseClass
from congregate.migration.meta.custom_importer.data_models.tree.author import Author

from gitlab_ps_utils.decorators import stable_retry
from gitlab_ps_utils.audit_logger import audit_logger
from gitlab_ps_utils.logger import myLogger
from gitlab_ps_utils.misc_utils import generate_audit_log_message
from gitlab_ps_utils.string_utils import deobfuscate

log = myLogger(__name__)
audit = audit_logger(__name__)


class CodeCommitApiWrapper(BaseClass):

    def __init__(self):
        super().__init__()
        
        if self.config.source_type and self.config.src_aws_region:
            # disable retries for BOTO3 as this is handled uniformly by @stable_retry for all APIs and API wrappers
            self.boto3_configuration = Config(region_name = self.config.src_aws_region, retries = dict(max_attempts = 0))
            # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
    
            self.boto_client = boto3.client('codecommit', config=self.boto3_configuration,
                                aws_access_key_id = self.config.src_aws_access_key_id,
                                aws_secret_access_key = self.config.src_aws_secret_access_key,
                                aws_session_token = self.config.src_aws_session_token)
        else:
            # Not CodeCommit or no region => skip building a Boto client
            self.boto_client = None
       
    @stable_retry
    def get_repository(self, project_id,repository_name, description=None):
        """
        Generates a Boto3 get_repository request to CodeCommit.
        You will need to provide the repository_id (string) and have AWS crentials configured, see:
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html

            :param project_id: (str) The ID of the project for the audit logger
            :param repository_id: (str) The ID of the repository
            :param description: (str) An optional description of the request for the audit logger. Defaults to None
            :return: The response object *not* the json() or text()
        """
        audit.info(generate_audit_log_message("Boto3", description, f"{project_id} get_repository: {repository_name}"))
        return self.boto_client.get_repository(repositoryName = repository_name)

    @stable_retry
    def get_all_repositories(self, project_id: str = None, description=None):
        """
        Generates Boto3 list_repositories requests in a paginated manner to CodeCommit.
        You will need to have AWS crentials configured, see:
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html

            :param project_id: (str) The ID of the project for the audit logger
            :param description: (str) An optional description of the request for the audit logger. Defaults to None
            :return: The list of all CodeCommit repositories
        """
       
        repositories = []
        next_token = None
        response = self.boto_client.list_repositories()
        repositories.extend(response['repositories'])
        while True:
            if next_token:
                audit.info(generate_audit_log_message("Boto3", description, f"{project_id} list_repositories: nextToken={next_token}"))
                response = self.boto_client.list_repositories(nextToken=next_token)
            else:
                audit.info(generate_audit_log_message("Boto3", description, f"{project_id} list_repositories: nextToken=None"))
                response = self.boto_client.list_repositories()

            repositories.extend(response['repositories'])

            next_token = response.get('nextToken', None)
            if not next_token:
                break

        return repositories
    

    @stable_retry
    def get_batch_repositories(self, 
                               repository_names: list = None,
                               description=None
        ) -> list:
        """
        Returns information about one or more repositories.
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/codecommit/client/batch_get_repositories.html
            :param repository_names: (str) REQUIRED The names of the repositories to get information about.
            :param description: (str) An optional description of the request for the audit logger. Defaults to None
            :return: The list of a batch or batches CodeCommit repositories
        """
        assert repository_names is not None, f"repository_names is {repository_names}, please provide a list of repositories"
        
        repositories = []
        response = self.boto_client.batch_get_repositories(repository_names)
        repositories.extend(response['repositories'])
        
        return repositories

    @stable_retry
    def get_all_pull_requests(self, project_id, repository_name, description=None):
        """
        Generates Boto3 list_pull_request requests in a paginated manner to CodeCommit.
        You will need to have AWS crentials configured, see:
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html

            :param project_id: (str) The ID of the project for the audit logger
            :param repository_name: (str) The name of the repository to generate the list of pull requests from
            :param description: (str) An optional description of the request for the audit logger. Defaults to None
            :return: The list of all CodeCommit repositories
        """
        pull_requests = []
        next_token = None
        while True:
            if next_token:
                audit.info(generate_audit_log_message("Boto3", description, f"{project_id} list_pull_requests: repositoryName={repository_name}, nextToken={next_token}"))
                response = self.boto_client.list_pull_requests(repositoryName=repository_name, nextToken=next_token)
            else:
                audit.info(generate_audit_log_message("Boto3", description, f"{project_id} list_pull_requests(): repositoryName={repository_name}, nextToken=None"))
                response = self.boto_client.list_pull_requests(repositoryName=repository_name)

            pull_requests.extend(response['pullRequestIds'])

            next_token = response.get('nextToken', None)
            if not next_token:
                break

        return pull_requests
    
    @stable_retry
    def get_pull_request(self, project_id, pull_request_id, description=None):
        """
        Generates a Boto3 get_pull_request request to CodeCommit.
        You will need to provide the rpull_request_id (string) and have AWS crentials configured, see:
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html

            :param project_id: (str) The ID of the project for the audit logger
            :param pull_request_id: (str) The ID of the pull request
            :param description: (str) An optional description of the request for the audit logger. Defaults to None
            :return: The response object *not* the json() or text()
        """
        audit.info(generate_audit_log_message("Boto3", description, f"{project_id} get_pull_request: {pull_request_id}"))
        return self.boto_client.get_pull_request(pullRequestId = pull_request_id)["pullRequest"]
    
    def get_detailed_pull_requests(self, project_id, repository_name, description=None):
        """
        Generates a list of pull requests with detailed PR information

            :param project_id: (str) The ID of the project for the audit logger
            :param repository_name: (str) The name of the repository to generate the list of pull requests from
            :return: The list of all CodeCommit pull requests for a repository
        """
        pr_list = []

        for pr in self.get_all_pull_requests(project_id, repository_name):
            detailed_pr = self.get_pull_request(project_id, pr)
            pr_list.append(detailed_pr)
        
        return pr_list
    
    @stable_retry
    def get_pull_request_diffs(self, project_id, repository_name, source_sha, target_sha, description=None):
        """
        Generates Boto3 call to retrieve all diffs for a pull request in a paginated manner from CodeCommit.
        You will need to have AWS crentials configured, see:
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html

            :param project_id: (str) The ID of the project for the audit logger
            :param repository_name: (str) The name of the repository to generate the list of pull requests from
            :param source_sha: (str) The source sha of the pull request
            :param target_sha: (str) The target sha of the pull request
            :param description: (str) An optional description of the request for the audit logger. Defaults to None
            :return: The list of all CodeCommit repositories
        """
        diffs = []
        next_token = None
        while True:
            if next_token:
                audit.info(generate_audit_log_message("Boto3", description, f"{project_id} get_differences(): repositoryName={repository_name}, nextToken={next_token}"))
                response = self.boto_client.get_differences(repositoryName=repository_name, beforeCommitSpecifier=source_sha, afterCommitSpecifier=target_sha, nextToken=next_token)
            else:
                audit.info(generate_audit_log_message("Boto3", description, f"{project_id} get_differences(): repositoryName={repository_name}, nextToken=None"))
                response = self.boto_client.get_differences(repositoryName=repository_name, beforeCommitSpecifier=source_sha, afterCommitSpecifier=target_sha)

            diffs.extend(response['differences'])

            next_token = response.get('nextToken', None)
            if not next_token:
                break

        return diffs

    @stable_retry
    def get_all_pull_request_threads(self, project_id, repository_name, pull_request_id, description=None):
        """
        Generates Boto3 get_comments_for_pull_request requests in a paginated manner to CodeCommit.
        You will need to have AWS crentials configured, see:
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html

            :param project_id: (str) The ID of the project for the audit logger
            :param repository_name: (str) The name of the repository to generate the list of pull requests from
            :param pull_request_id: (str) The id of the pull request to retrieve comments from
            :param description: (str) An optional description of the request for the audit logger. Defaults to None
            :return: The list of all CodeCommit repositories
        """
        pull_request_comments = []
        next_token = None
        while True:
            if next_token:
                audit.info(generate_audit_log_message("Boto3", description, f"{project_id} get_comments_for_pull_request: repositoryName={repository_name}, pullRequestID={pull_request_id}, nextToken={next_token}"))
                response = self.boto_client.get_comments_for_pull_requests(pullRequestId=pull_request_id, nextToken=next_token)
            else:
                audit.info(generate_audit_log_message("Boto3", description, f"{project_id} get_comments_for_pull_request(): repositoryName={repository_name}, pullRequestId={pull_request_id}, nextToken=None"))
                response = self.boto_client.get_comments_for_pull_request(pullRequestId=pull_request_id)

            pull_request_comments.extend(response['commentsForPullRequestData'])

            next_token = response.get('nextToken', None)
            if not next_token:
                break

        return pull_request_comments
    
    # Placeholder method - TBD
    def get_user_from_arn(self, arn):
        return Author(name="Mia Migrator", email="mia@migration.com")

