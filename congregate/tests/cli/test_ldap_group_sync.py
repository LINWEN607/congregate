import unittest
from unittest.mock import patch, PropertyMock
from pytest import mark
from congregate.cli.ldap_group_sync import LdapGroupSync
from congregate.helpers.conf import Config
from congregate.helpers.configuration_validator import ConfigurationValidator
from gitlab_ps_utils.api import GitLabApi


class MockPostResponseObject():
    def json(self):
        return {"abc": "def"}


@mark.unit_test
class LdapGroupSyncTests(unittest.TestCase):
    # pylint: disable=no-member
    def setUp(self):
        self.ldap = LdapGroupSync()

    def test_load_file_happy(self):
        self.ldap.load_pdv("congregate/tests/data/good_ldap.pdv")
        self.assertTrue(self.ldap.ldap_dict.get("01234") == "CN=x,OU=y")
        self.assertTrue(self.ldap.ldap_dict.get("56789") == "someCommonName")

    def test_load_file_incorrect_path_hard_fail(self):
        with self.assertRaises(FileNotFoundError):
            self.ldap.load_pdv("FAKE_FILE")

    def test_load_file_duplicate_group_id_logs_warning(self):
        with self.assertLogs(self.ldap.log) as cm:
            self.ldap.load_pdv("congregate/tests/data/dupe_group_id_ldap.pdv")
            self.assertTrue(self.ldap.ldap_dict.get("01234") == "CN=x,OU=y")
            self.assertTrue(self.ldap.ldap_dict.get(
                "56789") == "someCommonName")
        self.assertEqual(cm.output, [
                         "WARNING:congregate.helpers.base_class:group_id 56789 duplicated in file"])

    @patch.object(ConfigurationValidator, 'destination_token', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch.object(Config, 'ldap_group_link_provider', new_callable=PropertyMock)
    @patch.object(Config, 'ldap_group_link_group_access', new_callable=PropertyMock)
    def test_check_log_info_on_dry_run(self, ldap_group_link_group_access, ldap_group_link_provider, dstn_hostname, dstn_access_token):
        ldap_group_link_group_access.return_value = 10
        ldap_group_link_provider.return_value = "LDAP"
        dstn_hostname.return_value = "test.gitlab.com"
        dstn_access_token.return_value = "TOKEN"

        self.ldap.load_pdv("congregate/tests/data/good_ldap.pdv")

        with self.assertLogs(self.ldap.log) as cm:
            self.ldap.synchronize_groups()
        self.assertEqual(cm.output, [
            'INFO:congregate.helpers.base_class:Linking 01234 with CN=x,OU=y', 'INFO:congregate.helpers.base_class:Linking 56789 with someCommonName'
        ])

    @patch.object(ConfigurationValidator, 'destination_token', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch.object(GitLabApi, "generate_post_request")
    def test_load_config_gets_defaults(self, p, dstn_hostname, dstn_access_token):
        p.return_value = MockPostResponseObject()
        dstn_hostname.return_value = "test.gitlab.com"
        dstn_access_token.return_value = "TOKEN"
        self.ldap.load_pdv("congregate/tests/data/good_ldap.pdv")
        self.ldap.synchronize_groups(dry_run=False)
        self.assertEqual(self.ldap.ldap_results[0]["abc"], "def")
