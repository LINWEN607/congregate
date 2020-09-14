import unittest
import mock
import pytest
import responses
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.users import MockUsersApi
from congregate.tests.mockapi.gitlab.token import invalid_token
from congregate.tests.mockapi.gitlab.error import other_error
from congregate.helpers.exceptions import ConfigurationException


@pytest.mark.unit_test
class ConfigurationValidationTests(unittest.TestCase):
    # pylint: disable=no-member
    def setUp(self):
        self.groups = MockGroupsApi()
        self.users = MockUsersApi()
        self.config = ConfigurationValidator(
            path="congregate/tests/cli/data/test_not_ext_src_parent_group_path_no_mirror_name_aws_default.conf")

    @pytest.fixture(autouse=True)
    def reset_validation(self):
        ConfigurationValidator().dstn_parent_group_path_validated_in_session = False
        ConfigurationValidator().dstn_parent_id_validated_in_session = False
        ConfigurationValidator().import_user_id_validated_in_session = False

    @responses.activate
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_fail_parent_id_validation(self, url):
        self.config.dstn_parent_id_validated_in_session = False
        url_value = "https://gitlab.com/api/v4/groups/1234"
        url.return_value = url_value
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_id", "1234")
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.groups.get_group_404(), status=404, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertRaises(ConfigurationException,
                          self.config.validate_dstn_parent_group_id, 1234)

    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_succeed_parent_id_validation(self, url):
        self.config.dstn_parent_id_validated_in_session = False
        print(self.config.dstn_parent_id_validated_in_session)
        url_value = "https://gitlab.com/api/v4/groups/4"
        url.return_value = url_value
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_id", "1234")
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_path", "twitter")
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.groups.get_group(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertTrue(self.config.dstn_parent_id, 1234)

    @responses.activate
    # pylint: enable=no-member
    # @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_parent_group_path_validated_in_session')
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_succeed_parent_id_and_path_validation(self, url):
        self.config.dstn_parent_group_path_validated_in_session = True
        self.config.dstn_parent_id_validated_in_session = False
        url_value = "https://gitlab.com/api/v4/groups/4"
        url.return_value = url_value
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_id", "1234")
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_path", "twitter")
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.groups.get_group(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertTrue(self.config.dstn_parent_id, 1234)

    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_fail_import_user_id_validation(self, url):
        url_value = "https://gitlab.com/api/v4/users"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.users.get_user_404(), status=404, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        # self.assertRaises(ConfigurationException, self.config.validate_import_user_id, 1)
        with self.assertRaises(ConfigurationException) as context:
            self.config.import_user_id

        self.assertTrue(context.exception)

    def test_none_parent_id_validation(self):
        self.assertTrue(self.config.validate_dstn_parent_group_id(None))

    def test_none_import_user_id_validation(self):
        self.assertRaises(ConfigurationException,
                          self.config.validate_import_user_id, None)

    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_invalid_token(self, url):
        url_value = "https://gitlab.com/api/v4/users"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=invalid_token(), status=404, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertRaises(ConfigurationException,
                          self.config.validate_import_user_id, 1)

    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_unexpected_error(self, url):
        url_value = "https://gitlab.com/api/v4/users"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=other_error(), status=404, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertRaises(Exception, self.config.validate_import_user_id, 1)

    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_pass_import_user_id_validation(self, url):
        url_value = "https://gitlab.com/api/v4/users"
        url.return_value = url_value
        self.config.as_obj().set("DESTINATION", "import_user_id", "1")
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.users.get_current_user(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertTrue(self.config.import_user_id, 1)

    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_mismatched_import_user_id_validation(self, url):
        url_value = "https://gitlab.com/api/v4/users"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.users.get_current_user(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertRaises(ConfigurationException,
                          self.config.validate_import_user_id, 2)

    @responses.activate
    # pylint: enable=no-member
    @mock.patch.object(ConfigurationValidator, 'dstn_parent_id', new_callable=mock.PropertyMock)
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_succeed_parent_group_path_validation(self, url, parent_id):
        parent_id.return_value = 4
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_path", "twitter")
        url_value = "https://gitlab.com/api/v4/groups/4"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.groups.get_group(), status=200, content_type='text/json', match_querystring=True)
        responses.add(responses.GET, url_value,
                      json=self.groups.get_group(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertTrue(self.config.dstn_parent_group_path, "twitter")

    @responses.activate
    # pylint: enable=no-member
    @mock.patch.object(ConfigurationValidator, 'dstn_parent_id', new_callable=mock.PropertyMock)
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_fail_parent_group_path_validation(self, url, parent_id):
        parent_id.return_value = 4
        self.config.as_obj().set("DESTINATION", "dstn_parent_group_path", "twitter")
        url_value = "https://gitlab.com/api/v4/groups/4"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.groups.get_group(), status=200, content_type='text/json', match_querystring=True)
        responses.add(responses.GET, url_value,
                      json=self.groups.get_group(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
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
