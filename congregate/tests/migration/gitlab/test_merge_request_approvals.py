import unittest
from pytest import mark
import congregate.migration.gitlab.merge_request_approvals as mra


@mark.unit_test
class MergeRequestApprovalsTests(unittest.TestCase):

    def test_user_search_check_and_log_new_user_empty_returns_base_approver_ids(self):
        m = mra.MergeRequestApprovalsClient()
        with self.assertLogs(m.log, level="WARNING"):
            self.assertEqual(m.user_search_check_and_log(
                {}, {'email': "a@abc.com"}, [1, 2, 3], "email"), [1, 2, 3])

    def test_user_search_check_and_log_no_user_id_returns_base_approver_ids(self):
        m = mra.MergeRequestApprovalsClient()
        with self.assertLogs(m.log, level="WARNING"):
            self.assertEqual(m.user_search_check_and_log(
                {"noid": 1}, {'email': "a@abc.com"}, [1, 2, 3], "email"), [1, 2, 3])

    def test_user_search_check_and_log_happy(self):
        m = mra.MergeRequestApprovalsClient()
        self.assertEqual(m.user_search_check_and_log(
            {"id": 4}, {'email': "a@abc.com"}, [1, 2, 3], "email"), [1, 2, 3, 4])
