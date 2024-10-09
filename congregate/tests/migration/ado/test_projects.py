import unittest
from unittest.mock import Mock, patch
from congregate.migration.ado.projects import ProjectsClient  # Replace with the actual class name

class TestHandleRetrievingProject(unittest.TestCase):

    def setUp(self):
        self.projects = ProjectsClient()  # Replace with the actual class name
        self.projects.log = Mock()
        self.projects.api = Mock()
        self.projects.repositories_api = Mock()
        self.projects.base_api = Mock()
        self.projects.config = Mock()
        self.projects.config.source_host = "https://dev.azure.com/organization"

    def test_handle_retrieving_project_no_project(self):
        self.projects.handle_retrieving_project(None)
        self.projects.log.error.assert_called_once_with("Failed to retrieve project information")

    def test_handle_retrieving_project_no_repositories(self):
        project = {"id": "project_id"}
        self.projects.api.get_count.return_value = 0
        
        self.projects.handle_retrieving_project(project)
        
        self.projects.api.get_count.assert_called_once_with("project_id/_apis/git/repositories")
        self.projects.repositories_api.get_all_repositories.assert_not_called()

    @patch('congregate.migration.ado.projects.strip_netloc')
    def test_handle_retrieving_project_with_repositories(self, mock_strip_netloc):
        project = {"id": "project_id"}
        repository = {"name": "repo1"}
        mock_strip_netloc.return_value = "dev.azure.com-organization"
        self.projects.api.get_count.return_value = 1
        self.projects.repositories_api.get_all_repositories.return_value = [repository]
        self.projects.base_api.format_project.return_value = {"formatted": "project"}
        
        mock_mongo = Mock()
        
        self.projects.handle_retrieving_project(project, mock_mongo)
        
        self.projects.api.get_count.assert_called_once_with("project_id/_apis/git/repositories")
        self.projects.repositories_api.get_all_repositories.assert_called_once_with("project_id")
        self.projects.base_api.format_project.assert_called_once_with(project, repository, 1, mock_mongo)
        mock_mongo.insert_data.assert_called_once_with("projects-dev.azure.com-organization", {"formatted": "project"})

    @patch('congregate.migration.ado.projects.strip_netloc')
    def test_handle_retrieving_project_multiple_repositories(self, mock_strip_netloc):
        project = {"id": "project_id"}
        repositories = [{"name": "repo1"}, {"name": "repo2"}]
        mock_strip_netloc.return_value = "dev.azure.com-organization"
        self.projects.api.get_count.return_value = 2
        self.projects.repositories_api.get_all_repositories.return_value = repositories
        self.projects.base_api.format_project.side_effect = [{"formatted": "project1"}, {"formatted": "project2"}]
        
        mock_mongo = Mock()
        
        self.projects.handle_retrieving_project(project, mock_mongo)
        
        self.projects.api.get_count.assert_called_once_with("project_id/_apis/git/repositories")
        self.projects.repositories_api.get_all_repositories.assert_called_once_with("project_id")
        self.assertEqual(self.projects.base_api.format_project.call_count, 2)
        self.assertEqual(mock_mongo.insert_data.call_count, 2)
        mock_mongo.insert_data.assert_any_call("projects-dev.azure.com-organization", {"formatted": "project1"})
        mock_mongo.insert_data.assert_any_call("projects-dev.azure.com-organization", {"formatted": "project2"})

