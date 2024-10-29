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
from congregate.migration.ado.api.repositories import RepositoriesApi
from congregate.migration.ado.api.base import AzureDevOpsApiWrapper



@mark.unit_test
class ProjectsTests(unittest.TestCase):
    def setUp(self):
        self.mock_projects = MockProjectsApi()
        self.projects = ProjectsClient()
    @patch.object(CongregateMongoConnector, "close_connection")
    @patch.object(RepositoriesApi, "get_all_repositories")
    @patch.object(AzureDevOpsApiWrapper, "get_count")
    @patch('congregate.migration.ado.api.base.AzureDevOpsApiWrapper.generate_get_request')
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    def test_handle_retrieving_project(self, mock_user_token, mock_src_host, mock_dest_url,
                                   mock_generate_get_request, mock_get_count, mock_get_all_repositories, mock_close_connection):
        mock_dest_url.side_effect = ["http://gitlab.com", "http://gitlab.com"]
        mock_src_host.return_value = "https://dev.azure.com"
        mock_user_token.return_value = "username:password"
        
        mock_resp = MagicMock()
        mock_get_count.return_value = 1
        type(mock_resp).status_code = PropertyMock(return_value=200)
        mock_resp.json.side_effect = [
            {"displayId": "main"}, {"displayId": "main"}, {"displayId": "main"}, {"displayId": "main"}]
        
        mock_generate_get_request.return_value = mock_resp

        mock_get_all_repositories.return_value = self.mock_projects.get_all_repositories()

        expected_projects = [
            {
               "name": "AnotherRepository",
                "id": "5febef5a-833d-4e14-b9c0-14cb638f91e6",
                "path": "anotherrepository",
                "path_with_namespace": "azure-bicep-workshop",
                "visibility": "private",
                "description": "",
                "members": [],
                "http_url_to_repo": "https://dev.azure.com/gitlab-ps/_apis/repositories/AnotherRepository",
                "ssh_url_to_repo": "git@dev.azure.com:gitlab-ps/AnotherRepository.git",
                "lastUpdateTime": "2024-04-11T21:11:29.787Z",
                "namespace": ""
            }
        ]

        mock_close_connection.return_value = None

        listed_project = [self.mock_projects.get_single_project(
        )]

        mongo = CongregateMongoConnector(client=mongomock.MongoClient)
        for project in listed_project:
            self.projects.handle_retrieving_project(project, mongo=mongo)

        actual_projects = [d for d, _ in mongo.stream_collection(
            "projects-dev.azure.com")]
        print(f"actual projects: {actual_projects}")
        for i, _ in enumerate(expected_projects):
            print(f"in the loop: {actual_projects[i].items()}\n expected: {expected_projects[i].items()}")
            self.assertEqual(
                actual_projects[i].items(), expected_projects[i].items())

   