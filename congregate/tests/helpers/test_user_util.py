import unittest
import unittest.mock as mock
import pytest
import congregate.helpers.user_util as uutil

@pytest.mark.unit_test
class UserUtilTest(unittest.TestCase):
    @mock.patch("congregate.helpers.base_class.ConfigurationValidator.user_map", new_callable=unittest.mock.PropertyMock)
    def test_happy(self, um):
        um.return_value = "congregate/tests/helpers/user_util/data/fake_user_map.csv"
        with self.assertLogs('congregate.helpers.base_class') as captured:
            with mock.patch.object(uutil.bm, "app_path", "congregate/tests/helpers/user_util"):
                uutil.map_and_stage_users_by_email_match()
        self.assertEqual(len(captured.records), 7)
        self.assertIn(
            'INFO:congregate.helpers.base_class:DRY-RUN: Found 3 users to remap:\n{"id": 2, "name": "uname2", "username": "u.name2", "email": "new_email2@b.com"}\n{"id": 1, "name": "uname1", "username": "u.name1", "email": "new_email1@b.com"}\n{"id": 3, "name": "uname3", "username": "u.name3", "email": "new_email3@b.com"}',
            captured.output
        )
        self.assertIn('INFO:congregate.helpers.base_class:DRY-RUN: Found 0 users in the CSV not in staged_users: \n', captured.output)
        self.assertIn('INFO:congregate.helpers.base_class:DRY-RUN: 0 users will be removed from staging, and only the mapped will be staged', captured.output)

    @mock.patch("congregate.helpers.base_class.ConfigurationValidator.user_map", new_callable=unittest.mock.PropertyMock)
    def test_bad_in_csv(self, um):
        um.return_value = "congregate/tests/helpers/user_util/data/fake_user_map_extra.csv"
        with self.assertLogs('congregate.helpers.base_class') as captured:
            with mock.patch.object(uutil.bm, "app_path", "congregate/tests/helpers/user_util"):
                uutil.map_and_stage_users_by_email_match()
        self.assertEqual(len(captured.records), 7)
        self.assertIn(
            'INFO:congregate.helpers.base_class:DRY-RUN: Found 1 users in the CSV not in staged_users: \n{"old_email": "old_email4@a.com", "new_email": "new_email4@b.com"}', captured.output)
