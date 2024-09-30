import unittest
import warnings
from unittest.mock import patch, PropertyMock, MagicMock
from pytest import mark
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock
from congregate.helpers.congregate_mdbc import CongregateMongoConnector
from congregate.tests.mockapi.ado.projects import MockProjectsApi
from congregate.migration.ado.projects import ProjectsClient
from congregate.migration.ado.api.projects import ProjectsApi



@mark.unit_test
class ProjectsTests(unittest.TestCase):
    def setUp(self):
        self.mock_projects = MockProjectsApi()
        self.projects = ProjectsClient()

    @patch.object(CongregateMongoConnector, "close_connection")
    @patch.object(ProjectsApi, "get_all_projects")
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_handle_retrieving_project(self, mock_user_token, mock_src_host, mock_dest_url,
                                   mock_get_all_projects, mock_close_connection):
        mock_dest_url.side_effect = ["http://gitlab.com", "http://gitlab.com"]
        mock_src_host.return_value = "https://dev.azure.com"
        mock_user_token.return_value = "username:password"
        mock_resp = MagicMock()
        type(mock_resp).status_code = PropertyMock(return_value=200)
        mock_resp.json.side_effect = [
            {"displayId": "main"}, {"displayId": "main"}, {"displayId": "main"}, {"displayId": "main"}]
        mock_get_all_projects.return_value = self.mock_projects.get_single_project()
        expected_projects = [
            {
                "id": "20671faf-e1bd-4226-8172-0cdf0fdb7128",
                "name": "Azure Bicep Workshop",
                "url": "https://dev.azure.com/gitlab-ps/_apis/projects/20671faf-e1bd-4226-8172-0cdf0fdb7128",
                "state": "wellFormed",
                "revision": 29,
                "visibility": "private",
                "lastUpdateTime": "2024-04-11T21:11:29.787Z"
                
            }
        ]

        mock_close_connection.return_value = None

        listed_project = [self.mock_projects.get_single_project(
        )]

        mongo = CongregateMongoConnector(client=mongomock.MongoClient)
        for project in listed_project:
            self.projects.handle_retrieving_project(project, mongo=mongo)

        actual_projects = [d for d, _ in mongo.stream_collection(
            "groups-dev.azure.company.com")]
        print(actual_projects)

        for i, _ in enumerate(expected_projects):
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())

   