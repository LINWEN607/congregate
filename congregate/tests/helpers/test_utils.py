import unittest
from unittest import mock
from pytest import mark
import congregate.helpers.utils as utils
from congregate.tests.helpers.mock_data.results import MockProjectResults
from congregate.helpers.dict_utils import xml_to_dict
from congregate.tests.mockapi.jenkins.jobs import JenkinsJobsApi


@mark.unit_test
class UtilsTests(unittest.TestCase):

    def test_is_dot_com(self):
        assert utils.is_dot_com("asdasd") is False
        assert utils.is_dot_com("https://gitlab.com") is True

    def test_is_github_dot_com(self):
        assert utils.is_github_dot_com("asdasd") is False
        assert utils.is_github_dot_com("https://api.github.com") is True

    @mock.patch("os.getenv")
    @mock.patch("os.getcwd")
    def test_get_congregate_path_with_no_env_set(self, get_cwd, get_env):
        get_env.return_value = None
        get_cwd.return_value = "FAKEPATH"
        app_path = utils.get_congregate_path()
        self.assertEqual(app_path, "FAKEPATH")

    @mock.patch("os.getenv")
    def test_get_congregate_path_with_env_set(self, get_env):
        get_env.return_value = "FAKEPATH"
        app_path = utils.get_congregate_path()
        self.assertEqual(app_path, "FAKEPATH")

    @mock.patch("congregate.helpers.utils.read_json_file_into_object")
    @mock.patch("glob.glob")
    def test_stitch_json(self, glob, json):
        results = MockProjectResults()
        glob.return_value = [
            'project_migration_results_2020-05-05_22:17:45.335715.json',
            'project_migration_results_2020-05-05_21:38:04.565534.json',
            'project_migration_results_2020-05-05_21:17:42.719402.json',
            'project_migration_results_2020-05-05_19:26:18.616265.json',
            'project_migration_results_2020-04-28_23:06:02.139918.json'
        ]

        json.side_effect = [
            results.get_completely_failed_results(),
            results.get_partially_successful_results(),
            results.get_successful_results_subset()
        ]

        expected = results.get_completely_successful_results()
        actual = utils.stitch_json_results(steps=2)

        self.assertEqual(expected, actual)

    @mock.patch("congregate.helpers.utils.read_json_file_into_object")
    @mock.patch("glob.glob")
    def test_stitch_json_too_many_steps(self, glob, json):
        results = MockProjectResults()
        glob.return_value = [
            'project_migration_results_2020-05-05_22:17:45.335715.json',
            'project_migration_results_2020-05-05_21:38:04.565534.json',
            'project_migration_results_2020-05-05_21:17:42.719402.json',
            'project_migration_results_2020-05-05_19:26:18.616265.json',
            'project_migration_results_2020-04-28_23:06:02.139918.json'
        ]

        json.side_effect = [
            results.get_completely_failed_results(),
            results.get_partially_successful_results(),
            results.get_successful_results_subset(),
            [],
            []
        ]

        expected = results.get_completely_successful_results()
        actual = utils.stitch_json_results(steps=6)

        self.assertEqual(expected, actual)
    
    def test_xml_to_dict_complex(self):
        j = JenkinsJobsApi()
        test_xml = j.get_test_job_config_xml()
        expected = j.get_job_config_dict()

        actual = xml_to_dict(test_xml)

        self.assertEqual(expected, actual)