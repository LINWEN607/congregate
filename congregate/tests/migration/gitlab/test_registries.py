import unittest
from unittest import mock
from pytest import mark

from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.gitlab.registries import RegistryClient
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi


@mark.unit_test
class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.reg = RegistryClient()
        self.mock_projects = MockProjectsApi()

    @mock.patch.object(ConfigurationValidator, 'source_token', new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'destination_token', new_callable=mock.PropertyMock)
    @mock.patch.object(RegistryClient, "is_enabled")
    def test_enabled(self, enabled, dest_token, src_token):
        enabled.side_effect = [True, True, True,
                               False, False, True, False, False]
        dest_token.side_effect = ["token", "token", "token", "token"]
        src_token.side_effect = ["token", "token", "token", "token"]
        assert self.reg.are_enabled(1, 2) == (True, True)
        assert self.reg.are_enabled(1, 2) == (True, False)
        assert self.reg.are_enabled(1, 2) == (False, True)
        assert self.reg.are_enabled(1, 2) == (False, False)

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_parent_group_path', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url(self, registry, path):
        registry.return_value = "registry.test.com"
        path.return_value = "pmm-demo/spring-app-secure-2"
        project = self.mock_projects.get_staged_group_project()

        self.assertEqual(self.reg.generate_destination_registry_url(
            project), "registry.test.com/pmm-demo/spring-app-secure-2")

    @mock.patch("congregate.helpers.migrate_utils.get_dst_path_with_namespace")
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url_with_dest_group(self, registry, path):
        registry.return_value = "registry.test.com"
        path.return_value = "organization/pmm-demo/spring-app-secure-2"
        project = self.mock_projects.get_staged_group_project()

        self.assertEqual(self.reg.generate_destination_registry_url(
            project), "registry.test.com/organization/pmm-demo/spring-app-secure-2")

    @mock.patch("congregate.helpers.migrate_utils.get_dst_path_with_namespace")
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url_with_dest_group_uppercase(self, registry, path):
        registry.return_value = "registry.test.com"
        path.return_value = "ORGanization/pmm-demo/spring-app-secure-2"
        project = self.mock_projects.get_staged_group_project()

        self.assertEqual(self.reg.generate_destination_registry_url(
            project), "registry.test.com/organization/pmm-demo/spring-app-secure-2")

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url_with_target_namespace(self, registry):
        registry.return_value = "registry.test.com"
        project = self.mock_projects.get_staged_group_project_with_target_namespace()

        self.assertEqual(self.reg.generate_destination_registry_url(
            project), "registry.test.com/top-level-group/sub-level-group/pmm-demo/spring-app-secure-2")

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url_with_target_namespace_override(self, registry):
        registry.return_value = "registry.test.com"
        project = self.mock_projects.get_staged_group_project_with_target_namespace_override()

        self.assertEqual(self.reg.generate_destination_registry_url(
            project), "registry.test.com/top-level-group/sub-level-group/spring-app-secure-2")
