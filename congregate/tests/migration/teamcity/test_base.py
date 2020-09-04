import unittest
from mock import patch, PropertyMock
from congregate.tests.mockapi.teamcity.parameters import ParametersApi
from congregate.migration.teamcity.base import TeamcityClient


class BaseTests(unittest.TestCase):
    @patch('congregate.helpers.conf.Config.ci_source_type', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.ci_source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.ci_source_username', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.ci_source_token', new_callable=PropertyMock)
    def test_transform_ci_variables(self, token, username, host, source_type):
        token.return_value = 'abc123'
        username.return_value = 'abc123'
        host.return_value = 'http://example.teamcity.com/'
        source_type.return_value = 'abc123'
        params = ParametersApi()
        test_results = params.get_single_parameter()
        client = TeamcityClient()

        expected = {
            'environment_scope': 'teamcity',
            'key': 'Checkbox_Param',
            'masked': False,
            'protected': False,
            'value': "True",
            'variable_type': 'env_var'}
        actual = client.transform_ci_variables(test_results)
        self.assertDictEqual(expected, actual)

    @patch('congregate.helpers.conf.Config.ci_source_type', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.ci_source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.ci_source_username', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.ci_source_token', new_callable=PropertyMock)
    def test_transform_ci_variables_no_default_param(self, token, username, host, source_type):
        token.return_value = 'abc123'
        username.return_value = 'abc123'
        host.return_value = 'http://example.teamcity.com/'
        source_type.return_value = 'abc123'
        params = ParametersApi()
        test_results = params.get_single_parameter_no_default_param()
        client = TeamcityClient()

        expected = {
            'environment_scope': 'teamcity',
            'key': 'Masked_Param',
            'masked': False,
            'protected': False,
            'value': "No Default Value",
            'variable_type': 'env_var'}
        actual = client.transform_ci_variables(test_results)
        self.assertDictEqual(expected, actual)
