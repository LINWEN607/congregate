import unittest
from unittest.mock import patch, PropertyMock
from pytest import mark
from congregate.helpers.reporting import Reporting
from congregate.helpers.configuration_validator import ConfigurationValidator

@mark.unit_test
class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.reporting = Reporting(123)

    def test_check_tasks_match(self):
        '''
        This should be a successful match
        '''
        old = [{'repo_name': 'success'}, {'repo_name': 'unsuccessful'}]
        new = [{'repo_name': 'success'}, {'repo_name': 'unsuccessful'}]
        expected = []
        actual = self.reporting.check_existing_tasks(new, old)
        self.assertEqual(expected, actual)

    def test_check_tasks_all_new(self):
        '''
        This should be an UNSUCCESSFUL match
        '''
        old = []
        new = [{'repo_name': 'unsuccessful1'}, {'repo_name': 'unsuccessful2'}]
        actual = self.reporting.check_existing_tasks(new, old)
        self.assertEqual(new, actual)

    def test_modify_description(self):
        new_desc_sec = "Here is another section"
        existing_desc = "This is the original description"
        expected = f"{existing_desc}\n{new_desc_sec}"
        actual = self.reporting.modify_description(existing_desc, new_desc_sec)
        self.assertEqual(expected, actual)

    def test_modify_description_empty_string(self):
        existing_desc = "This is the original description"
        expected = f"{existing_desc}"
        actual = self.reporting.modify_description(existing_desc, "")
        self.assertEqual(expected, actual)

    def test_modify_description_no_change(self):
        existing_desc = "This is the original description"
        expected = f"{existing_desc}"
        actual = self.reporting.modify_description(existing_desc, None)
        self.assertEqual(expected, actual)

    @patch.object(ConfigurationValidator, "reporting", new_callable=PropertyMock)
    def test_subs_replace(self, mock_reporting):
        mock_reporting.return_value = {
            "subs": {
                "jira_page": "https://www.atlassian.com/"
            }
        }
        desc = """
            Refer to the [Jira Project]({{jira_page}}) for more information
        """
        expected = """
            Refer to the [Jira Project](https://www.atlassian.com/) for more information
        """
        actual = self.reporting.subs_replace("jira_page", desc)
        self.assertEqual(expected, actual)

    @patch.object(ConfigurationValidator, "reporting", new_callable=PropertyMock)
    def test_check_substitution(self, mock_reporting):
        mock_reporting.return_value = {
            "subs": {
                "jira_page": "https://www.atlassian.com/"
            }
        }
        desc = """
            Refer to the [Jira Project]({{jira_page}}) for more information
        """
        expected = """
            Refer to the [Jira Project](https://www.atlassian.com/) for more information
        """
        actual = self.reporting.check_substitutions(desc)
        self.assertEqual(expected, actual)

    @patch.object(ConfigurationValidator, "reporting", new_callable=PropertyMock)
    def test_check_substitution_unknown_var(self, mock_reporting):
        mock_reporting.return_value = {
            "subs": {
                "jira_page": "https://www.atlassian.com/"
            }
        }
        desc = """
            Refer to the [Jira Project]({{jira_page}}) for more information or
            this [other page]({{random_var}}) for additional information
        """
        expected = """
            Refer to the [Jira Project](https://www.atlassian.com/) for more information or
            this [other page]({{random_var}}) for additional information
        """
        actual = self.reporting.check_substitutions(desc)
        self.assertEqual(expected, actual)

    def test_format_assignees(self):
        example_assignees = [
            {
                "username": "jdoe",
                "random_key": "random_value"
            },
            {
                "username": "abaker",
                "random_key": "random_value"
            }
        ]
        expected = [
            {
                "name": "jdoe"
            },
            {
                "name": "abaker"
            }
        ]
        actual = self.reporting.format_assignees(example_assignees)

        self.assertListEqual(expected, actual)

