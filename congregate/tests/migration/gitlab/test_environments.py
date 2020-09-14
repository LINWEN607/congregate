import unittest
import pytest

from congregate.tests.mockapi.gitlab.environments import MockEnvironmentsApi
from congregate.migration.gitlab.environments import EnvironmentsClient

@pytest.mark.unit_test
class EnvironmentsTests(unittest.TestCase):
    def setUp(self):
        self.mock_environment = MockEnvironmentsApi()
        self.environment = EnvironmentsClient()

    def test_generate_environment_data(self):
        expected = {
            "name": "review/fix-foo",
            "external_url": "https://review-fix-foo-dfjre3.example.gitlab.com",
        }
        envs = list(self.mock_environment.get_all_environments_generator())
        actual = self.environment.generate_environment_data(envs[0][0])

        self.assertEqual(expected, actual)
