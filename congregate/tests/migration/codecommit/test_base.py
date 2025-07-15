# import unittest
# from unittest.mock import patch, MagicMock, PropertyMock
# import pytest
# from botocore.exceptions import ClientError

# from congregate.migration.codecommit.api.base import CodeCommitApiWrapper
# from congregate.helpers.base_class import BaseClass, ConfigurationValidator
# from congregate.migration.codecommit.base import CodeCommitWrapper


# @pytest.mark.unit_test
# class TestCodeCommitApiWrapper(unittest.TestCase):

#     @patch('congregate.helpers.conf.Config.source_type', new_callable=PropertyMock)
#     @patch('congregate.helpers.conf.Config.src_aws_region', new_callable=PropertyMock)
#     def setUp(self, mock_src_aws_region, mock_source_type):
#         """Set up a new instance of CodeCommitApiWrapper with mocks for Boto3 client."""
#         self.mock_boto_client = MagicMock()
#         mock_src_aws_region.return_value = "us-east-1"
#         mock_source_type.return_value = "codecommit"
#         with patch('boto3.client', return_value=self.mock_boto_client):
#             self.api_wrapper = CodeCommitApiWrapper()

#     @patch('gitlab_ps_utils.audit_logger.audit_logger')
#     def test_get_repository(self, mock_audit_info):
#         """Test get_repository calls Boto3 get_repository with correct parameters."""
#         mock_response = {"repositoryMetadata": {"repositoryName": "test-repo"}}
#         self.mock_boto_client.get_repository.return_value = mock_response
        
#         response = self.api_wrapper.get_repository("test-project", "test-repo")
        
#         self.mock_boto_client.get_repository.assert_called_once_with(repositoryName="test-repo")
#         # mock_audit_info.assert_called_with("Boto3: test-project get_repository: test-repo")  # Ensuring that the audit log is created
#         self.assertEqual(response, mock_response)
        
        
#     def test_get_batch_repositories(self):
#         """Test get_batch_repositories returns repository information."""
#         mock_response = {"repositories": [{"repositoryName": "repo1"}, {"repositoryName": "repo2"}]}
#         self.mock_boto_client.batch_get_repositories.return_value = mock_response
        
#         repositories = self.api_wrapper.get_batch_repositories(["repo1", "repo2"])
        
#         self.mock_boto_client.batch_get_repositories.assert_called_once_with(["repo1", "repo2"])
#         self.assertEqual(repositories, mock_response['repositories'])

#     def test_get_all_pull_requests(self):
#         """Test get_all_pull_requests returns a list of pull requests for a repository."""
#         mock_response = {"pullRequestIds": ["pr1", "pr2"], "nextToken": None}
#         self.mock_boto_client.list_pull_requests.return_value = mock_response
        
#         pull_requests = self.api_wrapper.get_all_pull_requests("test-project", "test-repo")
        
#         self.mock_boto_client.list_pull_requests.assert_called()  # Ensure the API was called
#         self.assertEqual(pull_requests, mock_response['pullRequestIds'])

#     @patch.object(ConfigurationValidator, 'src_token_validated_in_session', new_callable=PropertyMock)
#     @patch('gitlab_ps_utils.audit_logger.audit_logger')
#     def test_get_all_pull_request_threads(self, mock_audit_info, src_token):
#         """Test get_all_pull_request_threads returns comments for a pull request."""
#         src_token.return_value = True
#         mock_response = {"commentsForPullRequestData": [{"comment1": "data"}, {"comment2": "data"}]}
#         self.mock_boto_client.get_comments_for_pull_request.return_value = mock_response
        
#         comments = self.api_wrapper.get_all_pull_request_threads("test-project", "test-repo", "pr1")
        
#         self.mock_boto_client.get_comments_for_pull_request.assert_called_with(
#             pullRequestId="pr1"
#         )
#         self.assertEqual(comments, mock_response['commentsForPullRequestData'])




# @pytest.mark.unit_test
# class TestCodeCommitWrapper(unittest.TestCase):

#     def setUp(self):
#         """Set up a new instance of CodeCommitWrapper with mocks for dependent classes."""
#         self.mock_repositories_api = MagicMock()
#         self.mock_mongo_client = MagicMock()
        
#         with patch('congregate.migration.codecommit.base.CodeCommitApiWrapper', return_value=self.mock_repositories_api):
#             self.wrapper = CodeCommitWrapper()
#             self.wrapper.repositories_api = self.mock_repositories_api
#             self.wrapper.project = "test-project"


#     def test_slugify(self):
#         """Test slugify converts strings to URL-friendly format."""
#         self.assertEqual(self.wrapper.slugify("Hello World!"), "hello-world")
#         self.assertEqual(self.wrapper.slugify("   Trim  This "), "trim-this")
#         # self.assertEqual(self.wrapper.slugify("Multiple---Hyphens"), "multiple-hyphens")

#     def test_format_project(self):
#         """Test format_project formats project data correctly."""
#         project_name = "Test Project"
#         mock_repository = {
#             "repositoryMetadata": {
#                 "repositoryName": "Repo1",
#                 "repositoryId": "123",
#                 "cloneUrlHttp": "http://example.com/repo1.git",
#                 "cloneUrlSsh": "git@example.com:repo1.git",
#                 "defaultBranch": "main",
#                 "accountId": "12345"
#             }
#         }
        
#         result = self.wrapper.format_project(project_name, mock_repository, 1, None)
        
#         self.assertEqual(result['name'], "Repo1")
#         self.assertEqual(result['id'], "123")
#         self.assertEqual(result['http_url_to_repo'], "http://example.com/repo1.git")
#         self.assertEqual(result['ssh_url_to_repo'], "git@example.com:repo1.git")


