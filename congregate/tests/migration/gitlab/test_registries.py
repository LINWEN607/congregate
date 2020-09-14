import unittest
import pytest
import mock

from congregate.migration.gitlab.registries import RegistryClient

@pytest.mark.unit_test
class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.reg = RegistryClient()

    @mock.patch.object(RegistryClient, "is_enabled")
    def test_enabled(self, enabled):
        enabled.side_effect = [True, True, True, False, False, True, False, False]
        assert self.reg.are_enabled(1, 2) == (True, True)
        assert self.reg.are_enabled(1, 2) == (True, False)
        assert self.reg.are_enabled(1, 2) == (False, True)
        assert self.reg.are_enabled(1, 2) == (False, False)


    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_parent_group_path', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url(self, registry, path):
        registry.return_value = "registry.test.com"
        path.return_value = None
        suffix = "test_project"
        
        self.assertEqual(self.reg.generate_destination_registry_url(
            suffix).lower(), "registry.test.com/test_project")


    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_parent_group_path', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url_with_path(self, registry, path):
        registry.return_value = "registry.test.com"
        path.return_value = "organization"
        suffix = "test_project"
        
        self.assertEqual(self.reg.generate_destination_registry_url(
            suffix).lower(), "registry.test.com/organization/test_project")


    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_parent_group_path', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
    def test_new_registry_url_with_path_uppercase(self, registry, path):
        registry.return_value = "registry.test.com"
        path.return_value = "Organization"
        suffix = "test_project"

        self.assertEqual(self.reg.generate_destination_registry_url(
            suffix).lower(), "registry.test.com/organization/test_project")
