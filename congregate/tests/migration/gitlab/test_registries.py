import unittest
from unittest import mock
from pytest import mark

from congregate.migration.gitlab.registries import RegistryClient
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi


@mark.unit_test
class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.reg = RegistryClient()
        self.mock_projects = MockProjectsApi()

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_parent_group_path', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.source_registry', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url(self, dst_registry, src_registry, path):
        dst_registry.return_value = "registry.test.com"
        src_registry.return_value = "pse.tanuki.cloud"
        path.return_value = "pmm-demo/spring-app-secure-2"
        project = self.mock_projects.get_staged_group_project()
        suffix = "pse.tanuki.cloud/pmm-demo/spring-app-secure-2"

        self.assertEqual(self.reg.generate_destination_registry_url(
            project, suffix), "registry.test.com/pmm-demo/spring-app-secure-2")

    @mock.patch("congregate.helpers.migrate_utils.get_dst_path_with_namespace")
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.source_registry', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url_with_dest_group(self, dst_registry, src_registry, path):
        dst_registry.return_value = "registry.test.com"
        src_registry.return_value = "pse.tanuki.cloud"
        path.return_value = "organization/pmm-demo/spring-app-secure-2"
        project = self.mock_projects.get_staged_group_project()
        suffix = "pse.tanuki.cloud/pmm-demo/spring-app-secure-2"

        self.assertEqual(self.reg.generate_destination_registry_url(
            project, suffix), "registry.test.com/organization/pmm-demo/spring-app-secure-2")

    @mock.patch("congregate.helpers.migrate_utils.get_dst_path_with_namespace")
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.source_registry', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url_with_dest_group_uppercase(self, dst_registry, src_registry, path):
        dst_registry.return_value = "registry.test.com"
        src_registry.return_value = "pse.tanuki.cloud"
        path.return_value = "ORGanization/pmm-demo/spring-app-secure-2"
        project = self.mock_projects.get_staged_group_project()
        suffix = "pse.tanuki.cloud/pmm-demo/spring-app-secure-2"

        self.assertEqual(self.reg.generate_destination_registry_url(
            project, suffix), "registry.test.com/organization/pmm-demo/spring-app-secure-2")

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.source_registry', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url_with_target_namespace(self, dst_registry, src_registry):
        dst_registry.return_value = "registry.test.com"
        src_registry.return_value = "pse.tanuki.cloud"
        project = self.mock_projects.get_staged_group_project_with_target_namespace()
        suffix = "pse.tanuki.cloud/pmm-demo/spring-app-secure-2"

        self.assertEqual(self.reg.generate_destination_registry_url(
            project, suffix), "registry.test.com/top-level-group/sub-level-group/pmm-demo/spring-app-secure-2")

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.source_registry', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url_with_target_namespace_override(self, dst_registry, src_registry):
        dst_registry.return_value = "registry.test.com"
        src_registry.return_value = "pse.tanuki.cloud"
        project = self.mock_projects.get_staged_group_project_with_target_namespace_override()
        suffix = "pse.tanuki.cloud/pmm-demo/spring-app-secure-2"

        self.assertEqual(self.reg.generate_destination_registry_url(
            project, suffix), "registry.test.com/top-level-group/sub-level-group/spring-app-secure-2")
