import unittest
from unittest.mock import patch, PropertyMock, MagicMock
from pytest import mark
from httpx import RequestError

from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.gitlab.branches import BranchesClient
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi
from congregate.migration.gitlab.api.projects import ProjectsApi


@mark.unit_test
class BranchesTests(unittest.TestCase):
    def setUp(self):
        self.branches = BranchesClient()
        self.mock_projects = MockProjectsApi()

    @patch("congregate.helpers.migrate_utils.read_json_file_into_object")
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token', new_callable=PropertyMock)
    def test_set_default_branch_no_default_branch(self, mock_host, mock_token, mock_staged):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        mock_staged.return_value = self.mock_projects.get_staged_project_no_default_branch()
        with self.assertLogs(self.branches.log, level="WARNING"):
            self.branches.set_default_branch(dry_run=False)

    @patch.object(ProjectsApi, "set_default_project_branch")
    @patch("congregate.helpers.migrate_utils.read_json_file_into_object")
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token', new_callable=PropertyMock)
    def test_set_default_branch_exception(self, mock_host, mock_token, mock_staged, mock_set):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        mock_staged.return_value = self.mock_projects.get_staged_projects()
        mock_set.side_effect = RequestError("Failed")
        with self.assertLogs(self.branches.log, level="ERROR"):
            self.branches.set_default_branch(dry_run=False)

    @patch.object(ProjectsApi, "set_default_project_branch")
    @patch("congregate.helpers.migrate_utils.read_json_file_into_object")
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token', new_callable=PropertyMock)
    def test_set_default_branch(self, mock_host, mock_token, mock_staged, mock_set):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        mock_staged.return_value = self.mock_projects.get_staged_projects()

        mock_resp = MagicMock()
        type(mock_resp).status_code = PropertyMock(return_value=200)
        mock_resp.json.return_value = self.mock_projects.get_project()
        mock_set.side_effect = [mock_resp, mock_resp, mock_resp]
        self.assertIsNone(self.branches.set_default_branch(
            name="develop", dry_run=False))

    @patch.object(ProjectsApi, "set_default_project_branch")
    @patch("congregate.helpers.migrate_utils.read_json_file_into_object")
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, 'destination_token', new_callable=PropertyMock)
    def test_set_default_branch_error(self, mock_host, mock_token, mock_staged, mock_set):
        mock_host.return_value = "https://gitlabdestination.com"
        mock_token.return_value = "token"
        mock_staged.return_value = self.mock_projects.get_staged_projects()

        mock_resp = MagicMock()
        type(mock_resp).status_code = PropertyMock(return_value=404)
        mock_resp.json.return_value = self.mock_projects.get_project()
        mock_set.side_effect = [mock_resp, mock_resp, mock_resp]
        with self.assertLogs(self.branches.log, level="ERROR"):
            self.branches.set_default_branch(dry_run=False)
