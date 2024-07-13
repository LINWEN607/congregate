import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from congregate.migration.gitlab.issue_links import IssueLinksClient
from pytest import mark
import warnings

# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock

class MockProjectsApi:
    def get_all_projects(self):
        return [
            {"id": 1, "name": "Project1"},
            {"id": 2, "name": "Project2"},
            {"id": 3, "name": "Project3"}
        ]

class MockGitLabApiWrapper:
    def __init__(self):
        self.projects_api = MockProjectsApi()


@mark.unit_test
class ProjectMigrationTests(unittest.TestCase):
    def setUp(self):
        self.api_wrapper = MockGitLabApiWrapper()
        self.issue_links = IssueLinksClient(DRY_RUN=False)

    @patch('congregate.helpers.conf.Config.prop')
    @patch('congregate.helpers.configuration_validator.ConfigurationValidator.validate_dstn_token', return_value=True)
    @patch('congregate.helpers.configuration_validator.ConfigurationValidator.validate_src_token_gitlab', return_value=None)
    @patch('requests.get')
    @patch('requests.post')
    @patch('congregate.migration.gitlab.api.issue_links.IssueLinksApi.create_issue_link')
    @patch('congregate.migration.gitlab.api.issue_links.IssueLinksApi.list_issue_links')
    @patch('congregate.migration.gitlab.api.issues.IssuesApi.get_all_project_issues')
    def test_migrate_issue_links(self, mock_get_all_project_issues, mock_list_issue_links, mock_create_issue_link, mock_requests_post, mock_requests_get, mock_validate_src_token_gitlab, mock_validate_dest_token, mock_prop):
        dest_project_id = 10
        project_id_mapping = {
            "1": 10,
            "2": 20,
            "3": 30
        }

        # Mock configuration values
        mock_prop.side_effect = lambda section, key, default=None, obfuscated=False: {
            ("DESTINATION", "dstn_access_token"): "mocked_dest_token",
            ("DESTINATION", "dstn_hostname"): "mocked_dest_host"
        }.get((section, key), default)

        # Mock the requests to prevent actual HTTP requests
        mock_requests_get.return_value = MagicMock(status_code=200, json=lambda: {})
        mock_requests_post.return_value = MagicMock(status_code=201)

        mock_get_all_project_issues.return_value = [
            {"iid": 1, "title": "Issue 1", "description": "Description 1"},
            {"iid": 2, "title": "Issue 2", "description": "Description 2"}
        ]
        mock_list_issue_links.return_value = MagicMock(json=lambda: [
            {"project_id": 2, "iid": 5, "link_type": "relates_to"},
            {"project_id": 3, "iid": 7, "link_type": "blocks"}
        ])
        mock_create_issue_link.return_value = MagicMock(status_code=201)

        self.issue_links.migrate_issue_links(project_id_mapping)

        mock_create_issue_link.assert_any_call('mocked_dest_host', 'mocked_dest_token', dest_project_id, 1, 20, 5, "relates_to")
        mock_create_issue_link.assert_any_call('mocked_dest_host', 'mocked_dest_token', dest_project_id, 1, 30, 7, "blocks")
