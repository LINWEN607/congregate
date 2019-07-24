import mock

from congregate.migration.gitlab.registries import RegistryClient


reg = RegistryClient()

@mock.patch.object(RegistryClient, "is_enabled")
def test_enabled(enabled):
    enabled.side_effect = [True, True, True, False, False, True, False, False]
    assert reg.enabled(1, 2) == True
    assert reg.enabled(1, 2) == False
    assert reg.enabled(1, 2) == False
    assert reg.enabled(1, 2) == False
