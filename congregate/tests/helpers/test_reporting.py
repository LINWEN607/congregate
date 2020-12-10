import unittest
import pytest
from congregate.helpers.reporting import Reporting

@pytest.mark.unit_test
class ReportingTests(unittest.TestCase):
    '''
    '''

    def setUp(self):
        self.reporting = Reporting()

    def test_check_tasks_match(self):
        '''
        This should be a successful match
        '''
        repo_name = "success"
        tasks_match = [{'repo_name': 'success'}, {'repo_name': 'unsuccessful'}]
        expected = True
        actual = self.reporting.check_existing_tasks(tasks_match, repo_name)
        self.assertEqual(expected, actual)

    def test_check_tasks_nomatch(self):
        '''
        This should be an UNSUCCESSFUL match
        '''
        repo_name = "success"
        tasks_match = [{'repo_name': 'unsuccessful1'}, {'repo_name': 'unsuccessful2'}]
        actual = self.reporting.check_existing_tasks(tasks_match, repo_name)
        self.assertIsNone(actual)
