import mock

from congregate.migration.gitlab.registries import RegistryClient
from congregate.helpers.configuration_validator import ConfigurationValidator

reg = RegistryClient()

@mock.patch.object(RegistryClient, "is_enabled")
def test_enabled(enabled):
    enabled.side_effect = [True, True, True, False, False, True, False, False]
    assert reg.are_enabled(1, 2) == (True, True)
    assert reg.are_enabled(1, 2) == (True, False)
    assert reg.are_enabled(1, 2) == (False, True)
    assert reg.are_enabled(1, 2) == (False, False)

@mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dest_parent_group_path', new_callable=mock.PropertyMock)
@mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
def test_new_registry_url(registry, path):
    registry.return_value = "registry.test.com"
    path.return_value = None
    suffix = "test_project"
    assert reg.generate_destination_registry_url(suffix).lower() == "registry.test.com/test_project"

@mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dest_parent_group_path', new_callable=mock.PropertyMock)
@mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
def test_new_registry_url_with_path(registry, path):
    registry.return_value = "registry.test.com"
    path.return_value = "organization"
    suffix = "test_project"
    assert reg.generate_destination_registry_url(suffix).lower() == "registry.test.com/organization/test_project"

@mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dest_parent_group_path', new_callable=mock.PropertyMock)
@mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.destination_registry', new_callable=mock.PropertyMock)
def test_new_registry_url_with_path_uppercase(registry, path):
    registry.return_value = "registry.test.com"
    path.return_value = "Organization"
    suffix = "test_project"
    assert reg.generate_destination_registry_url(suffix).lower() == "registry.test.com/organization/test_project"
