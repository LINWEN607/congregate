import unittest
from unittest.mock import Mock
from pytest import mark

from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.migration.ado.api.projects import ProjectsApi
from congregate.migration.ado.api.repositories import RepositoriesApi

from congregate.tests.mockapi.ado.projects import MockProjectsApi
from congregate.tests.mockapi.ado.groups import MockGroupsApi

@mark.unit_test
class BaseTests(unittest.TestCase):

    def setUp(self):
        self.mock_projects = MockProjectsApi()
        self.api = AzureDevOpsApiWrapper()
        self.projects_api = ProjectsApi()
        self.repositories_api = RepositoriesApi()
        self.api.slugify = Mock(side_effect=lambda x: x.lower().replace(' ', '-'))

    def test_slugify(self):
        self.assertEqual(self.api.slugify("Yet Another Repo"), "yet-another-repo")

    def test_format_project(self):
        # TODO add format_project_tests
        self.assertEqual(MockProjectsApi.get_formated_project, MockProjectsApi.get_formated_project)
        
    def test_format_group(self):
        # TODO add format_group_tests
         self.assertEqual(MockGroupsApi.get_formated_group, MockGroupsApi.get_formated_group)

