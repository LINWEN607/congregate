import pytest
from unittest import TestCase
from unittest.mock import MagicMock, patch
from congregate.helpers.congregate_mdbc import CongregateMongoConnector
from congregate.migration.codecommit.projects import CodeCommitProjectsClient
from congregate.migration.codecommit.api.base import CodeCommitApiWrapper
from congregate.migration.codecommit.base import CodeCommitWrapper
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi

@pytest.mark.unit_test
class TestProjectsClient(TestCase):
    """Test cases for ProjectsClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.projects_api = ProjectsClient()
        # Mock the required components
        self.mock_api = MagicMock(spec=CodeCommitApiWrapper)
        self.mock_base_api = MagicMock(spec=CodeCommitWrapper)
        self.mock_merge_requests = MagicMock(spec=MergeRequestsApi)
        self.mock_mongo = MagicMock(spec=CongregateMongoConnector)
        
        # Set the mocked components
        self.projects_api.api = self.mock_api
        self.projects_api.base_api = self.mock_base_api
        self.projects_api.merge_requests_api = self.mock_merge_requests
        self.projects_api.mongo = self.mock_mongo

    def test_retrieve_project_info_no_processes(self):
        """Test retrieving project info without specifying processes."""
        with patch.object(ProjectsClient, 'handle_retrieving_project') as mock_handle:
            self.projects_api.retrieve_project_info()
            mock_handle.assert_called_once_with("CodeCommit")

    def test_handle_retrieving_project_no_project(self):
        """Test handling project retrieval with no project provided."""
        with self.assertLogs(self.projects_api.log, level="ERROR") as log:
            self.projects_api.handle_retrieving_project(None, mongo=self.mock_mongo)
            self.assertIn("Failed to retrieve project information", log.output[0])

    def test_handle_retrieving_project_no_repositories(self):
        """Test handling project retrieval with no repositories."""
        # Mock API to return empty repository list
        self.mock_api.get_all_repositories.return_value = []
        
        result = self.projects_api.handle_retrieving_project("CodeCommit", mongo=self.mock_mongo)
        self.assertIsNone(result)
        self.mock_api.get_all_repositories.assert_called_once_with("CodeCommit")

    @patch('congregate.migration.codecommit.projects.strip_netloc')
    def test_handle_retrieving_project_success(self, mock_strip_netloc):
        """Test successful project retrieval and storage."""
        # Mock data
        test_repos = [
            {"repositoryName": "repo1"},
            {"repositoryName": "repo2"}
        ]
        detailed_repos = [
            {"repositoryMetadata": {"repositoryName": "repo1", "repositoryId": "123"}},
            {"repositoryMetadata": {"repositoryName": "repo2", "repositoryId": "456"}}
        ]
        formatted_projects = [
            {"name": "repo1", "id": "123"},
            {"name": "repo2", "id": "456"}
        ]

        # Setup mocks
        self.mock_api.get_all_repositories.return_value = test_repos
        self.mock_api.get_repository.side_effect = detailed_repos
        self.mock_base_api.format_project.side_effect = formatted_projects
        mock_strip_netloc.return_value = "codecommit.amazonaws.com"

        # Call method
        self.projects_api.handle_retrieving_project("CodeCommit", mongo=self.mock_mongo)

        # Verify API calls
        self.mock_api.get_all_repositories.assert_called_once_with("CodeCommit")
        self.assertEqual(self.mock_api.get_repository.call_count, 2)
        self.assertEqual(self.mock_base_api.format_project.call_count, 2)

        # Verify MongoDB insertions
        expected_collection = "projects-codecommit.amazonaws.com"
        self.assertEqual(self.mock_mongo.insert_data.call_count, 2)
        for i, formatted_project in enumerate(formatted_projects):
            self.mock_mongo.insert_data.assert_any_call(expected_collection, formatted_project)

    @patch('congregate.migration.codecommit.projects.strip_netloc')
    def test_handle_retrieving_project_with_invalid_repository(self, mock_strip_netloc):
        """Test project retrieval with an invalid repository in the list."""
        # Mock data
        test_repos = [{"repositoryName": "repo1"}, {"repositoryName": "invalid_repo"}]
        self.mock_api.get_all_repositories.return_value = test_repos
        self.mock_api.get_repository.side_effect = [
            {"repositoryMetadata": {"repositoryName": "repo1", "repositoryId": "123"}},
            None
        ]
        self.mock_base_api.format_project.return_value = {"name": "repo1", "id": "123"}
        mock_strip_netloc.return_value = "codecommit.amazonaws.com"

        # Call method
        self.projects_api.handle_retrieving_project("CodeCommit", mongo=self.mock_mongo)

        # Verify only valid repository was processed
        self.assertEqual(self.mock_base_api.format_project.call_count, 1)
        self.assertEqual(self.mock_mongo.insert_data.call_count, 1)