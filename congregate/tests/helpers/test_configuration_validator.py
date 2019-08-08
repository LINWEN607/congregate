import unittest
import mock
import requests
import responses
import json
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.helpers.mockapi.groups import MockGroupsApi
from congregate.helpers.mockapi.users import MockUsersApi
from congregate.helpers.mockapi.token import invalid_token
from congregate.helpers.mockapi.error import other_error
from congregate.helpers.exceptions import ConfigurationException
from congregate.helpers.api import generate_v4_request_url


class ConfigurationValidationTests(unittest.TestCase):
    # pylint: disable=no-member
    def setUp(self):
        self.groups = MockGroupsApi()
        self.users = MockUsersApi()
        self.config = ConfigurationValidator()

    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_fail_parent_id_validation(self, url):
        url_value = "https://gitlab.com/api/v4/groups/1234"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                  json=self.groups.get_group_404(), status=404, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertRaises(ConfigurationException, self.config.parent_id, 1234)

    
    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_succeed_parent_id_validation(self, url):
        url_value = "https://gitlab.com/api/v4/groups/1234"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                  json=self.groups.get_group(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertTrue(self.config.validate_parent_group_id(4))

    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_fail_parent_user_id_validation(self, url):
        url_value = "https://gitlab.com/api/v4/users"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                  json=self.users.get_user_404(), status=404, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        # self.assertRaises(ConfigurationException, self.config.validate_parent_user_id, 1)
        with self.assertRaises(ConfigurationException) as context:
            self.config.parent_user_id

        self.assertTrue(context.exception)

    def test_no_parent_user_id_validation(self):
        self.assertRaises(ConfigurationException, self.config.validate_parent_user_id, None)

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
        self.assertRaises(ConfigurationException, self.config.validate_parent_user_id, 1)

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
        self.assertRaises(Exception, self.config.validate_parent_user_id, 1)

    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_pass_parent_user_validation(self, url):
        url_value = "https://gitlab.com/api/v4/users"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                  json=self.users.get_current_user(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertTrue(self.config.validate_parent_user_id(1))

    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_mismatched_parent_user_id_validation(self, url):
        url_value = "https://gitlab.com/api/v4/users"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                  json=self.users.get_current_user(), status=200, content_type='text/json', match_querystring=True)
        # pylint: enable=no-member
        self.assertRaises(ConfigurationException, self.config.validate_parent_user_id, 2)

    