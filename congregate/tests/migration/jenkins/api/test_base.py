import unittest
from pytest import mark
from congregate.migration.jenkins.api.base import JenkinsApi

@mark.unit_test
class JenkinsApiBaseTests(unittest.TestCase):
    def test_strip_url(self):
        api = JenkinsApi(None, None, None)
        test_url = "https://jenkins.example.com/job/test-job"

        expected = "job/test-job"
        actual = api.strip_url(test_url)

        self.assertEqual(expected, actual)

    def test_strip_url_with_jenkins_path(self):
        api = JenkinsApi(None, None, None)
        test_url = "https://jenkins.example.com/jenkins/job/test-job"

        expected = "job/test-job"
        actual = api.strip_url(test_url)

        self.assertEqual(expected, actual)
    
    def test_strip_url_with_trailing_slash(self):
        api = JenkinsApi(None, None, None)
        test_url = "https://jenkins.example.com/jenkins/job/test-job/"

        expected = "job/test-job/"
        actual = api.strip_url(test_url)

        self.assertEqual(expected, actual)