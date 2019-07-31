import unittest
import mock
import requests
import responses
import json
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.helpers.mockapi.groups import MockGroupsApi
from congregate.helpers.exceptions import ConfigurationException
from congregate.helpers.api import generate_v4_request_url


class ConfigurationValidationTests(unittest.TestCase):
    # pylint: disable=no-member
    def setUp(self):
        self.groups = MockGroupsApi()
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

    