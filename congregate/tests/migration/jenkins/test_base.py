import unittest
import pytest
from mock import patch, PropertyMock
import warnings
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock
from congregate.tests.mockapi.jenkins.parameters import ParametersApi
from congregate.tests.mockapi.jenkins.jobs import JenkinsJobsApi
from congregate.migration.jenkins.base import JenkinsClient
from congregate.helpers.mdbc import MongoConnector


class JenkinsBaseTests(unittest.TestCase):
    @pytest.mark.unit_test
    @patch('congregate.helpers.conf.Config.jenkins_ci_source_type', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.jenkins_ci_source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.jenkins_ci_source_username', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.jenkins_ci_source_token', new_callable=PropertyMock)
    def test_transform_ci_variables(self, token, username, host, source_type):
        token.return_value = 'abc123'
        username.return_value = 'abc123'
        host.return_value = 'http://example.jenkins.com/'
        source_type.return_value = 'abc123'
        params = ParametersApi()
        test_results = params.get_single_parameter()
        client = JenkinsClient(host, username, token)

        expected = {
            'environment_scope': 'jenkins-0.0.0.0',
            'key': 'Boolean_Parameter',
            'masked': False,
            'protected': False,
            'value': "True",
            'variable_type': 'env_var'}
        actual = client.transform_ci_variables(test_results, "0.0.0.0")
        self.assertDictEqual(expected, actual)

    @pytest.mark.unit_test
    @patch('congregate.helpers.conf.Config.jenkins_ci_source_type', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.jenkins_ci_source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.jenkins_ci_source_username', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.jenkins_ci_source_token', new_callable=PropertyMock)
    def test_transform_ci_variables_no_default_param(self, token, username, host, source_type):
        token.return_value = 'abc123'
        username.return_value = 'abc123'
        host.return_value = 'http://example.jenkins.com/'
        source_type.return_value = 'abc123'
        params = ParametersApi()
        test_results = params.get_single_parameter_no_default_param()
        client = JenkinsClient(host, username, token)

        expected = {
            'environment_scope': 'jenkins-0.0.0.0',
            'key': 'run_parameter',
            'masked': False,
            'protected': False,
            'value': "No Default Value",
            'variable_type': 'env_var'}
        actual = client.transform_ci_variables(test_results, '0.0.0.0')
        self.assertDictEqual(expected, actual)

    # Mark as integration test.
    @patch('congregate.helpers.conf.Config.jenkins_ci_source_type', new_callable=PropertyMock)
    @patch.object(MongoConnector, "close_connection")
    @pytest.mark.jenkins_it
    def test_retrieve_jobs_with_scm_info(self, close_connection, source_type):
        token = 'password'
        username = 'test-admin'
        host = 'http://jenkins-test:8080'
        source_type.return_value = 'abc123'
        params = JenkinsJobsApi()
        expected = params.get_jobs_with_scm_info()
        client = JenkinsClient(host, username, token)
        close_connection.return_value = None
        mongo = MongoConnector(host="test-server", port=123456, client=mongomock.MongoClient)
        for job in client.jenkins_api.list_all_jobs():
            client.handle_retrieving_jenkins_jobs(job, mongo=mongo)
        actual = [d for d, _ in mongo.stream_collection("jenkins-jenkins-test:8080")]
        self.assertListEqual(expected, actual)

