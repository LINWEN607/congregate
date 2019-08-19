import mock

from congregate.migration.gitlab.registries import RegistryClient


reg = RegistryClient()

@mock.patch.object(RegistryClient, "is_enabled")
def test_enabled(enabled):
    enabled.side_effect = [True, True, True, False, False, True, False, False]
    assert reg.are_enabled(1, 2) == (True, True)
    assert reg.are_enabled(1, 2) == (True, False)
    assert reg.are_enabled(1, 2) == (False, True)
    assert reg.are_enabled(1, 2) == (False, False)
