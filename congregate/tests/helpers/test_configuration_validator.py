from io import StringIO
import unittest
from unittest import mock
from pytest import mark, fixture
import responses
import respx
from httpx import MockTransport, Response
from gitlab_ps_utils.exceptions import ConfigurationException
from gitlab_ps_utils.string_utils import obfuscate
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.users import MockUsersApi as GLMockUsers
from congregate.tests.mockapi.gitlab.settings import MockAppSettingsApi as GLMockSettings
from congregate.tests.mockapi.github.users import MockUsersApi as GHMockUsers
from congregate.tests.mockapi.bitbucket.users import MockUsersApi as BBSUsers
from congregate.tests.mockapi.ado.users import MockUsersApi as ADOUsers
from congregate.tests.mockapi.gitlab.token import invalid_token
from congregate.tests.mockapi.gitlab.error import other_error

@mark.unit_test
class ConfigurationValidationTests(unittest.TestCase):
    def setUp(self):
        self.groups = MockGroupsApi()
        self.users = GLMockUsers()
        self.github_users = GHMockUsers()
        self.gl_settings = GLMockSettings()
        self.bbs_users = BBSUsers()
        self.ado_users = ADOUsers()
        self.config = ConfigurationValidator(
            path="congregate/tests/cli/data/test_not_ext_src_parent_group_path_no_mirror_name_aws_default.conf")

    @fixture(autouse=True)
    def capsys(self, capsys):
        """Capsys hook into this class"""
        self.capsys = capsys

    @fixture(autouse=True)
    def reset_validation(self):
        ConfigurationValidator().dstn_parent_group_path_validated_in_session = False
        ConfigurationValidator().dstn_parent_id_validated_in_session = False
        ConfigurationValidator().import_user_id_validated_in_session = False

    @respx.mock
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_fail_parent_id_validation(self, url):
        self.config.dstn_parent_id_validated_in_session = False
        url_value = "https://gitlab.example.com/api/v4/groups/1234"
        url.return_value = url_value
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_id", "1234")
        fail_response = Response(404, json=self.groups.get_group_404())
        respx.get(url_value).mock(return_value=fail_response)

        self.assertRaises(ConfigurationException,
                        self.config.validate_dstn_parent_group_id, 1234)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.validate_dstn_token')
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_succeed_parent_id_validation(self, url, valid_token):
        self.config.dstn_parent_id_validated_in_session = False
        url_value = "https://gitlab.example.com/api/v4/groups/4"
        url.return_value = url_value
        valid_token.return_value = True
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_id", "1234")
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_path", "twitter")
        response = Response(200, json=self.groups.get_subgroup())
        respx.get(url_value).mock(return_value=response)
        self.assertTrue(self.config.dstn_parent_id, 1234)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.validate_dstn_token')
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_succeed_parent_id_and_path_validation(self, url, valid_token):
        self.config.dstn_parent_group_path_validated_in_session = True
        self.config.dstn_parent_id_validated_in_session = False
        url_value = "https://gitlab.example.com/api/v4/groups/4"
        url.return_value = url_value
        valid_token.return_value = True
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_id", "1234")
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_path", "twitter")

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.groups.get_group()
        ))

        self.assertTrue(self.config.dstn_parent_id, 1234)

    @respx.mock
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_fail_import_user_id_validation(self, url):
        url_value = "https://gitlab.example.com/api/v4/users"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=404,
            json=self.users.get_user_404()
        ))

        with self.assertRaises(ConfigurationException) as context:
            self.config.import_user_id
        self.assertTrue(context.exception)

    def test_none_parent_id_validation(self):
        self.assertTrue(self.config.validate_dstn_parent_group_id(None))

    def test_none_import_user_id_validation(self):
        self.assertRaises(ConfigurationException,
                          self.config.validate_import_user_id, None)

    @respx.mock
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_invalid_token(self, url):
        url_value = "https://gitlab.example.com/api/v4/users"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=404,
            json=invalid_token()
        ))

        self.assertRaises(ConfigurationException,
                          self.config.validate_import_user_id, 1)

    @respx.mock
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_unexpected_error(self, url):
        url_value = "https://gitlab.example.com/api/v4/users"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=404,
            json=other_error()
        ))

        self.assertRaises(Exception, self.config.validate_import_user_id, 1)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.validate_dstn_token')
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_pass_import_user_id_validation(self, url, valid_token):
        url_value = "https://gitlab.example.com/api/v4/users"
        url.return_value = url_value
        valid_token.return_value = True
        self.config.as_obj().set("DESTINATION", "import_user_id", "1")

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_current_user()
        ))

        self.assertTrue(self.config.import_user_id, 1)

    @respx.mock
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_mismatched_import_user_id_validation(self, url):
        url_value = "https://gitlab.example.com/api/v4/users"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_current_user()
        ))

        self.assertRaises(ConfigurationException,
                          self.config.validate_import_user_id, 2)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.validate_dstn_token')
    @mock.patch.object(ConfigurationValidator,
                       'dstn_parent_id', new_callable=mock.PropertyMock)
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_succeed_parent_group_path_validation(
            self, url, parent_id, valid_token):
        parent_id.return_value = 4
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_path", "twitter")
        url_value = "https://gitlab.example.com/api/v4/groups/4"
        url.return_value = url_value
        valid_token.return_value = True

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.groups.get_subgroup()
        ))

        self.assertTrue(self.config.dstn_parent_group_path, "twitter")

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.validate_dstn_token')
    @mock.patch.object(ConfigurationValidator,
                       'dstn_parent_id', new_callable=mock.PropertyMock)
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_fail_parent_group_path_validation_public(
            self, url, parent_id, valid_token):
        parent_id.return_value = 4
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_path", "twitter")
        url_value = "https://gitlab.example.com/api/v4/groups/4"
        url.return_value = url_value
        valid_token.return_value = True

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.groups.get_group()
        ))

        self.assertRaises(ConfigurationException,
                          self.config.validate_dstn_parent_group_path, "twitter")

    @respx.mock
    @mock.patch.object(ConfigurationValidator,
                       'dstn_parent_id', new_callable=mock.PropertyMock)
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_fail_parent_group_path_validation(self, url, parent_id):
        parent_id.return_value = 4
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_path", "twitter")
        url_value = "https://gitlab.example.com/api/v4/groups/4"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.groups.get_group()
        ))

        self.assertRaises(ConfigurationException,
                          self.config.validate_dstn_parent_group_path, "not-twitter")

    def test_none_parent_group_path_validation(self):
        self.assertTrue(self.config.validate_dstn_parent_group_path(None))

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_parent_group_path_validated_in_session')
    def test_already_validated_parent_group_path_validation(self, validated):
        validated.return_value = True
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_path", "twitter")
        self.config.dstn_parent_group_path_validated_in_session = True
        self.assertEqual(self.config.dstn_parent_group_path, "twitter")

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_parent_id_validated_in_session')
    def test_already_validated_parent_id_validation(self, validated):
        validated.return_value = True
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_id", "5")
        self.config.dstn_parent_id_validated_in_session = True
        self.assertEqual(self.config.dstn_parent_id, 5)

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.import_user_id_validated_in_session')
    def test_already_validated_import_user_id_validation(self, validated):
        validated.return_value = True
        self.config.as_obj().set("DESTINATION", "import_user_id", "1")
        self.config.import_user_id_validated_in_session = True
        self.assertEqual(self.config.import_user_id, 1)

    @respx.mock
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_validate_gitlab_src_token_invalid(self, url, secret, src_type):
        secret.return_value = "test"
        src_type.return_value = "gitlab"
        self.config.src_token_validated_in_session = False
        url_value = "https://gitlab.example.com/api/v4/user"
        url.return_value = url_value
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))

        respx.get(url_value).mock(return_value=Response(
            status_code=401,
            json=self.users.get_user_401()
        ))

        self.assertRaises(ConfigurationException,
                          self.config.validate_src_token, "test")

    @responses.activate
    # pylint: enable=no-member
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_host',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'ssl_verify',
                       new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    def test_validate_github_src_token_invalid(
            self, secret, verify, host, src_type):
        secret.return_value = "test"
        src_type.return_value = "github"
        verify.return_value = False
        host.return_value = "https://github.test.com"
        self.config.src_token_validated_in_session = False
        url_value = "https://github.test.com/api/v3/user"
        # url.return_value = url_value
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.github_users.get_user_401(), status=401, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertRaises(ConfigurationException,
                          self.config.validate_src_token, "test")

    @responses.activate
    # pylint: enable=no-member
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_host',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'ssl_verify',
                       new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    def test_validate_github_src_token_not_admin(
            self, secret, verify, host, src_type):
        secret.return_value = "test"
        src_type.return_value = "github"
        verify.return_value = False
        host.return_value = "https://github.test.com"
        self.config.src_token_validated_in_session = False
        url_value = "https://github.test.com/api/v3/user"
        # url.return_value = url_value
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.github_users.get_non_admin_user(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertRaises(ConfigurationException,
                          self.config.validate_src_token, "test")

    @responses.activate
    # pylint: enable=no-member
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_host',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'ssl_verify',
                       new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    def test_validate_github_src_token_success(
            self, secret, verify, host, src_type):
        secret.return_value = "test"
        src_type.return_value = "github"
        verify.return_value = False
        host.return_value = "https://api.github.com"
        self.config.src_token_validated_in_session = False
        url_value = "https://api.github.com/user"
        # url.return_value = url_value
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.github_users.get_non_admin_user(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertTrue(self.config.source_token, "test")

    @responses.activate
    # pylint: enable=no-member
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_host',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator,
                       'source_username', new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    def test_validate_bbs_src_token_invalid(
            self, secret, username, host, src_type):
        secret.return_value = "test"
        src_type.return_value = "bitbucket server"
        username.return_value = "admin"
        host.return_value = "https://bitbucket.server.com"
        self.config.src_token_validated_in_session = False
        url_value = "https://bitbucket.server.com/rest/api/1.0/admin/permissions/users?filter=admin"
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.bbs_users.get_user_401(), status=401, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertRaises(ConfigurationException,
                          self.config.validate_src_token, "test")

    @responses.activate
    # pylint: enable=no-member
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_host',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator,
                       'source_username', new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    def test_validate_bbs_src_token_user_invalid_group_invalid(
            self, secret, username, host, src_type):
        secret.return_value = "test"
        src_type.return_value = "bitbucket server"
        username.return_value = "non-user"
        host.return_value = "https://bitbucket.server.com"
        self.config.src_token_validated_in_session = False
        url_value = "https://bitbucket.server.com/rest/api/1.0/admin/permissions/users?filter=non-user"
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.bbs_users.get_user_invalid(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        url_value = "https://bitbucket.server.com/rest/api/1.0/admin/users/more-members?context=non-user"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.bbs_users.get_user_invalid(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertRaises(ConfigurationException,
                          self.config.validate_src_token, "test")

    @responses.activate
    # pylint: enable=no-member
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_host',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator,
                       'source_username', new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    def test_validate_bbs_src_token_not_sys_admin(
            self, secret, username, host, src_type):
        secret.return_value = "test"
        src_type.return_value = "bitbucket server"
        username.return_value = "non-admin"
        host.return_value = "https://bitbucket.server.com"
        self.config.src_token_validated_in_session = False
        url_value = "https://bitbucket.server.com/rest/api/1.0/admin/permissions/users?filter=non-admin"
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.bbs_users.get_non_admin_user(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertRaises(ConfigurationException,
                          self.config.validate_src_token, "test")

    @responses.activate
    # pylint: enable=no-member
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_host',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator,
                       'source_username', new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    def test_validate_bbs_src_token_success(
            self, secret, username, host, src_type):
        secret.return_value = "test"
        src_type.return_value = "bitbucket server"
        username.return_value = "admin"
        host.return_value = "https://bitbucket.server.com"
        self.config.src_token_validated_in_session = False
        url_value = "https://bitbucket.server.com/rest/api/1.0/admin/permissions/users?filter=admin"
        # url.return_value = url_value
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.bbs_users.get_sys_admin_user(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertTrue(self.config.source_token, "test")

    @responses.activate
    # pylint: enable=no-member
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_host',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator,
                       'source_username', new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    def test_validate_bbs_src_token_user_invalid_group_valid_success(
            self, secret, username, host, src_type):
        secret.return_value = "test"
        src_type.return_value = "bitbucket server"
        username.return_value = "non-user"
        host.return_value = "https://bitbucket.server.com"
        self.config.src_token_validated_in_session = False
        url_value = "https://bitbucket.server.com/rest/api/1.0/admin/permissions/users?filter=non-user"
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.bbs_users.get_user_invalid(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        url_value = "https://bitbucket.server.com/rest/api/1.0/admin/users/more-members?context=non-user"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.bbs_users.get_user_group(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        url_value = "https://bitbucket.server.com/rest/api/1.0/admin/permissions/groups?filter=admin-group"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.bbs_users.get_admin_group(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertTrue(self.config.source_token, "test")

    @respx.mock
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_validate_gitlab_src_token_not_admin(self, url, secret, src_type):
        secret.return_value = "test"
        src_type.return_value = "gitlab"
        self.config.src_token_validated_in_session = False
        url_value = "https://gitlab.example.com/api/v4/user"
        url.return_value = url_value
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_current_user()
        ))

        self.config.validate_src_token('test')

        # Capture warning stdout
        out, _ = self.capsys.readouterr()
        self.assertEqual(
            out, "Source token is currently assigned to a non-admin user. Some API endpoints (e.g. users) may be forbidden\n")

    @respx.mock
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_host',
                       new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    def test_validate_ado_src_token_success(
            self, secret, host, src_type):
        secret.return_value = "test"
        src_type.return_value = "azure devops"
        host.return_value = "https://dev.azure.com/gitlab-ps"
        self.config.src_token_validated_in_session = False
        url_value = "https://dev.azure.com/gitlab-ps/_apis/ConnectionData?api-version=7.2-preview"
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.ado_users.get_connection_data()
        ))

        self.assertTrue(self.config.source_token, "test")

    @respx.mock
    @mock.patch.object(ConfigurationValidator, 'source_type',
                       new_callable=mock.PropertyMock)
    @mock.patch("getpass.getpass")
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_validate_gitlab_src_token_success(self, url, secret, src_type):
        secret.return_value = "test"
        src_type.return_value = "gitlab"
        self.config.src_token_validated_in_session = False
        url_value = "https://gitlab.example.com/api/v4/user"
        url.return_value = url_value
        self.config.as_obj().set("SOURCE", "source_token", obfuscate("Enter secret: "))

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_admin_user()
        ))

        self.assertTrue(self.config.source_token, "test")

    def test_validate_src_token(self):
        self.assertTrue(self.config.validate_src_token(None))

    @mock.patch("getpass.getpass")
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session')
    def test_src_token_validated_in_session(self, validated, secret):
        secret.return_value = "test"
        validated.return_value = True
        self.config.as_obj().set("SOURCE", "src_access_token", obfuscate("Enter secret: "))
        self.config.src_token_validated_in_session = True
        self.assertEqual(self.config.source_token, "test")

    @respx.mock
    @mock.patch("getpass.getpass")
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_validate_dstn_token_invalid(self, url, secret):
        secret.return_value = "test"
        self.config.dstn_token_validated_in_session = False
        url_value = "https://gitlab.example.com/api/v4/user"
        url.return_value = url_value
        self.config.as_obj().set("DESTINATION", "destination_token",
                                 obfuscate("Enter secret: "))

        respx.get(url_value).mock(return_value=Response(
            status_code=401,
            json=self.users.get_user_401()
        ))

        self.assertRaises(ConfigurationException,
                          self.config.validate_dstn_token, "test")

    @respx.mock
    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch("getpass.getpass")
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_validate_dstn_token_not_admin(self, url, secret, stdout):
        secret.return_value = "test"
        self.config.dstn_token_validated_in_session = False
        url_value = "https://gitlab.example.com/api/v4/user"
        url.return_value = url_value
        self.config.as_obj().set("DESTINATION", "destination_token",
                                 obfuscate("Enter secret: "))

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_current_user()
        ))

        self.config.validate_dstn_token("test")
        expected = "Destination token is currently assigned to a non-admin user. Some API endpoints (e.g. users) may be forbidden\n"
        self.assertEqual(stdout.getvalue(), expected)

    @respx.mock
    @mock.patch("getpass.getpass")
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_validate_dstn_token_success(self, url, secret):
        secret.return_value = "test"
        self.config.dstn_token_validated_in_session = False
        url_value = "https://gitlab.example.com/api/v4/user"
        url.return_value = url_value
        self.config.as_obj().set("DESTINATION", "destination_token",
                                 obfuscate("Enter secret: "))

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_admin_user()
        ))

        self.assertTrue(self.config.destination_token, "test")

    def test_validate_dstn_token(self):
        self.assertTrue(self.config.validate_dstn_token(None))

    @mock.patch("getpass.getpass")
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session')
    def test_dstn_token_validated_in_session(self, validated, secret):
        secret.return_value = "test"
        validated.return_value = True
        self.config.as_obj().set("DESTINATION", "dstn_access_token",
                                 obfuscate("Enter secret: "))
        self.config.dstn_token_validated_in_session = True
        self.assertEqual(self.config.destination_token, "test")

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session')
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session')
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    @mock.patch.object(InstanceApi, "get_application_settings")
    def test_direct_transfer_all_good_admin(self, app_settings, url, src_token, dstn_token):
        # Mock validate src and dstn tokens
        src_token.return_value = True
        dstn_token.return_value = True
        url_value = "htts://gitlab.example.com/api/v4/user"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_admin_user()
        ))

        # Set direct_transfer to true to trigger validation
        self.config.as_obj().set("APP", "direct_transfer", "true")

        # Set up mock src settings API call
        src_setting_resp = mock.MagicMock()
        type(src_setting_resp).status_code = mock.PropertyMock(return_value=200)
        src_setting_resp.json.return_value = self.gl_settings.application_settings()

        # Set up mock dstn settings API call
        dstn_setting_resp = mock.MagicMock()
        type(dstn_setting_resp).status_code = mock.PropertyMock(return_value=200)
        dstn_setting_resp.json.return_value = self.gl_settings.application_settings()

        # Add mock objects to get_application_settings side effects
        app_settings.side_effect = [src_setting_resp, dstn_setting_resp]

        self.assertTrue(self.config.direct_transfer)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session')
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session')
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_direct_transfer_all_good_non_admin(self, url, src_token, dstn_token):
        # Mock validate src and dstn tokens
        src_token.return_value = True
        dstn_token.return_value = True
        url_value = "htts://gitlab.example.com/api/v4/user"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_current_user()
        ))

        # Set direct_transfer to true to trigger validation
        self.config.as_obj().set("APP", "direct_transfer", "true")

        self.assertTrue(self.config.direct_transfer)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session')
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session')
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    @mock.patch.object(InstanceApi, "get_application_settings")
    def test_direct_transfer_not_enabled_on_dstn(self, app_settings, url, src_token, dstn_token):
        # Mock validate src and dstn tokens
        src_token.return_value = True
        dstn_token.return_value = True
        url_value = "htts://gitlab.example.com/api/v4/user"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_admin_user()
        ))

        # Set direct_transfer to true to trigger validation
        self.config.as_obj().set("APP", "direct_transfer", "true")

        # Set up mock src settings API call
        src_setting_resp = mock.MagicMock()
        type(src_setting_resp).status_code = mock.PropertyMock(return_value=200)
        src_setting_resp.json.return_value = self.gl_settings.application_settings()

        # Set up mock dstn settings API call, this time mocking bulk import is disabled on dstn
        set_to_false = self.gl_settings.application_settings()
        set_to_false['bulk_import_enabled'] = False
        dstn_setting_resp = mock.MagicMock()
        type(dstn_setting_resp).status_code = mock.PropertyMock(return_value=200)
        dstn_setting_resp.json.return_value = set_to_false

        # Add mock objects to get_application_settings side effects
        app_settings.side_effect = [src_setting_resp, dstn_setting_resp]

        self.assertRaises(ConfigurationException,
                          self.config.validate_direct_transfer_enabled)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session')
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session')
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    @mock.patch.object(InstanceApi, "get_application_settings")
    def test_direct_transfer_not_enabled_on_src(self, app_settings, url, src_token, dstn_token):
        # Mock validate src and dstn tokens
        src_token.return_value = True
        dstn_token.return_value = True
        url_value = "htts://gitlab.example.com/api/v4/user"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_admin_user()
        ))

        # Set direct_transfer to true to trigger validation
        self.config.as_obj().set("APP", "direct_transfer", "true")

        # Set up mock src settings API call, this time mocking bulk import is disabled on src
        set_to_false = self.gl_settings.application_settings()
        set_to_false['bulk_import_enabled'] = False
        src_setting_resp = mock.MagicMock()
        type(src_setting_resp).status_code = mock.PropertyMock(return_value=200)
        src_setting_resp.json.return_value = set_to_false

        # Set up mock dstn settings API call
        dstn_setting_resp = mock.MagicMock()
        type(dstn_setting_resp).status_code = mock.PropertyMock(return_value=200)
        dstn_setting_resp.json.return_value = self.gl_settings.application_settings()

        # Add mock objects to get_application_settings side effects
        app_settings.side_effect = [src_setting_resp, dstn_setting_resp]

        self.assertRaises(ConfigurationException,
                          self.config.validate_direct_transfer_enabled)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session')
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session')
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    @mock.patch.object(InstanceApi, "get_application_settings")
    def test_direct_transfer_mismatched_download_size_warning(self, app_settings, url, src_token, dstn_token):
        # Mock validate src and dstn tokens
        src_token.return_value = True
        dstn_token.return_value = True
        url_value = "htts://gitlab.example.com/api/v4/user"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_admin_user()
        ))

        # Set direct_transfer to true to trigger validation
        self.config.as_obj().set("APP", "direct_transfer", "true")

        # Set up mock src settings API call
        src_setting_resp = mock.MagicMock()
        type(src_setting_resp).status_code = mock.PropertyMock(return_value=200)
        src_setting_resp.json.return_value = self.gl_settings.application_settings()

        # Set up mock dstn settings API call, this time setting the download size to a different size than src
        set_to_false = self.gl_settings.application_settings()
        set_to_false['bulk_import_max_download_file_size'] = 1024
        dstn_setting_resp = mock.MagicMock()
        type(dstn_setting_resp).status_code = mock.PropertyMock(return_value=200)
        dstn_setting_resp.json.return_value = set_to_false
        app_settings.side_effect = [src_setting_resp, dstn_setting_resp]

        self.assertTrue(self.config.direct_transfer)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session')
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session')
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    @mock.patch.object(InstanceApi, "get_application_settings")
    def test_direct_transfer_unknown_dest_settings(self, app_settings, url, src_token, dstn_token):
        # Mock validate src and dstn tokens
        src_token.return_value = True
        dstn_token.return_value = True
        url_value = "htts://gitlab.example.com/api/v4/user"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_admin_user()
        ))

        # Set direct_transfer to true to trigger validation
        self.config.as_obj().set("APP", "direct_transfer", "true")

        # Set up mock src settings API call
        src_setting_resp = mock.MagicMock()
        type(src_setting_resp).status_code = mock.PropertyMock(return_value=200)
        src_setting_resp.json.return_value = self.gl_settings.application_settings()

        # Set up empty dstn settings API call
        dstn_setting_resp = mock.MagicMock()
        type(dstn_setting_resp).status_code = mock.PropertyMock(return_value=403)
        dstn_setting_resp.json.return_value = None
        app_settings.side_effect = [src_setting_resp, dstn_setting_resp]

        self.assertTrue(self.config.direct_transfer)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session')
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session')
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    @mock.patch.object(InstanceApi, "get_application_settings")
    def test_direct_transfer_unknown_src_settings(self, app_settings, url, src_token, dstn_token):
        # Mock validate src and dstn tokens
        src_token.return_value = True
        dstn_token.return_value = True
        url_value = "htts://gitlab.example.com/api/v4/user"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_admin_user()
        ))

        # Set direct_transfer to true to trigger validation
        self.config.as_obj().set("APP", "direct_transfer", "true")

        # Set up mock src settings API call
        src_setting_resp = mock.MagicMock()
        type(src_setting_resp).status_code = mock.PropertyMock(return_value=403)
        src_setting_resp.json.return_value = None

        # Set up empty dstn settings API call
        dstn_setting_resp = mock.MagicMock()
        type(dstn_setting_resp).status_code = mock.PropertyMock(return_value=200)
        dstn_setting_resp.json.return_value = self.gl_settings.application_settings()
        app_settings.side_effect = [src_setting_resp, dstn_setting_resp]

        self.assertTrue(self.config.direct_transfer)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session')
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session')
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    @mock.patch.object(InstanceApi, "get_application_settings")
    def test_direct_transfer_unknown_src_dest(self, app_settings, url, src_token, dstn_token):
        # Mock validate src and dstn tokens
        src_token.return_value = True
        dstn_token.return_value = True
        url_value = "htts://gitlab.example.com/api/v4/user"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_admin_user()
        ))

        # Set direct_transfer to true to trigger validation
        self.config.as_obj().set("APP", "direct_transfer", "true")

        # Set up mock src settings API call, this time mocking bulk import is disabled on src
        src_setting_resp = mock.MagicMock()
        type(src_setting_resp).status_code = mock.PropertyMock(return_value=403)
        src_setting_resp.json.return_value = None

        # Set up mock dstn settings API call
        dstn_setting_resp = mock.MagicMock()
        type(dstn_setting_resp).status_code = mock.PropertyMock(return_value=403)
        dstn_setting_resp.json.return_value = None

        # Add mock objects to get_application_settings side effects
        app_settings.side_effect = [src_setting_resp, dstn_setting_resp]

        self.assertRaises(ConfigurationException,
                          self.config.validate_direct_transfer_enabled)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session')
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session')
    @mock.patch.object(ConfigurationValidator, 'destination_host', new_callable=mock.PropertyMock)
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    @mock.patch.object(InstanceApi, "get_application_settings")
    def test_direct_transfer_gitlab_dot_com_admin(self, app_settings, url, dest_host, src_token, dstn_token):
        # Mock validate src and dstn tokens
        dest_host.return_value = 'https://gitlab.com'
        src_token.return_value = True
        dstn_token.return_value = True
        url_value = "htts://gitlab.example.com/api/v4/user"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_admin_user()
        ))

        # Set direct_transfer to true to trigger validation
        self.config.as_obj().set("APP", "direct_transfer", "true")

        # Set up mock src settings API call
        src_setting_resp = mock.MagicMock()
        type(src_setting_resp).status_code = mock.PropertyMock(return_value=200)
        src_setting_resp.json.return_value = self.gl_settings.application_settings()

        # Add mock objects to get_application_settings side effects
        app_settings.side_effect = [src_setting_resp]

        self.assertTrue(self.config.direct_transfer)

    @respx.mock
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session')
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session')
    @mock.patch.object(ConfigurationValidator, 'destination_host', new_callable=mock.PropertyMock)
    @mock.patch("gitlab_ps_utils.api.generate_v4_request_url")
    def test_direct_transfer_gitlab_dot_com_non_admin(self, url, dest_host, src_token, dstn_token):
        # Mock validate src and dstn tokens
        dest_host.return_value = 'https://gitlab.com'
        src_token.return_value = True
        dstn_token.return_value = True
        url_value = "htts://gitlab.example.com/api/v4/user"
        url.return_value = url_value

        respx.get(url_value).mock(return_value=Response(
            status_code=200,
            json=self.users.get_current_user()
        ))

        # Set direct_transfer to true to trigger validation
        self.config.as_obj().set("APP", "direct_transfer", "true")

        self.assertTrue(self.config.direct_transfer)


def mock_api(*side_effect):
    mock_handler = mock.Mock()
    mock_handler.side_effect = side_effect
    transport = MockTransport(mock_handler)
    return mock_handler, transport
