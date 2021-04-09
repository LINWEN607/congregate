import unittest
from unittest.mock import patch, PropertyMock
from pytest import mark
from congregate.tests.mockapi.teamcity.parameters import ParametersApi
from congregate.tests.mockapi.teamcity.buildconfigs import TeamcityJobsApi
from congregate.migration.teamcity.base import TeamcityClient


class TeamCityBaseTests(unittest.TestCase):
    @mark.unit_test
    @patch('congregate.helpers.conf.Config.tc_ci_source_type', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.tc_ci_source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.tc_ci_source_username', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.tc_ci_source_token', new_callable=PropertyMock)
    def test_transform_ci_variables(self, token, username, host, source_type):
        token.return_value = 'abc123'
        username.return_value = 'abc123'
        url = 'http://example.teamcity.com'
        host.return_value = url
        source_type.return_value = 'abc123'
        params = ParametersApi()
        test_results = params.get_single_parameter()
        client = TeamcityClient(host, username, token)

        expected = {
            'environment_scope': 'teamcity-example.teamcity.com',
            'key': 'Checkbox_Param',
            'masked': False,
            'protected': False,
            'value': "true",
            'variable_type': 'env_var'}
        actual = client.transform_ci_variables(test_results, url)
        self.assertDictEqual(expected, actual)

    @mark.unit_test
    @patch('congregate.helpers.conf.Config.tc_ci_source_type', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.tc_ci_source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.tc_ci_source_username', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.tc_ci_source_token', new_callable=PropertyMock)
    def test_transform_ci_variables_no_default_param(self, token, username, host, source_type):
        token.return_value = 'abc123'
        username.return_value = 'abc123'
        url = 'http://example.teamcity.com'
        host.return_value = url
        source_type.return_value = 'abc123'
        params = ParametersApi()
        test_results = params.get_single_parameter_no_default_param()
        client = TeamcityClient(host, username, token)

        expected = {
            'environment_scope': 'teamcity-example.teamcity.com',
            'key': 'Masked_Param',
            'masked': False,
            'protected': False,
            'value': "No Default Value",
            'variable_type': 'env_var'}
        actual = client.transform_ci_variables(test_results, url)
        self.assertDictEqual(expected, actual)

    # @patch('congregate.helpers.conf.Config.tc_ci_source_type', new_callable=PropertyMock)
    # @patch('congregate.helpers.conf.Config.tc_ci_source_host', new_callable=PropertyMock)
    # @patch('congregate.helpers.conf.Config.tc_ci_source_username', new_callable=PropertyMock)
    # @patch('congregate.helpers.conf.Config.tc_ci_source_token', new_callable=PropertyMock)
    # def test_retrieve_jobs_with_vcs_info(self, token, username, host, source_type):
    #     token.return_value = 'abc123'
    #     username.return_value = 'abc123'
    #     host.return_value = 'http://example.teamcity.com/'
    #     source_type.return_value = 'abc123'
    #     params = TeamcityJobsApi()
    #     expected = params.get_job_config_dict()
    #     client = TeamcityClient(host, username, token)

    #     actual = client.retrieve_jobs_with_vcs_info()
    #     self.assertDictEqual(expected, actual)
