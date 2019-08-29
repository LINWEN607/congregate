import unittest
import congregate.migration.gitlab.merge_request_approvers as mra


# TODO: Mock logging capture
class MergeRequestApproversTests(unittest.TestCase):

    @staticmethod
    def test_user_search_check_and_log_new_user_empty_returns_base_approver_ids():
        m = mra.MergeRequestApproversClient()
        assert m.user_search_check_and_log([], {'email': "a@abc.com"}, [1, 2, 3]) == [1, 2, 3]

    @staticmethod
    def test_user_search_check_and_log_no_user_id_returns_base_approver_ids():
        m = mra.MergeRequestApproversClient()
        assert m.user_search_check_and_log([{"noid": 1}], {'email': "a@abc.com"}, [1, 2, 3]) == [1, 2, 3]

    @staticmethod
    def test_user_search_check_and_log_happy():
        m = mra.MergeRequestApproversClient()
        assert m.user_search_check_and_log([{"id": 4}], {'email': "a@abc.com"}, [1, 2, 3]) == [1, 2, 3, 4]

    @staticmethod
    def test_user_search_check_and_log_empty_user_returns_base_approver_ids():
        m = mra.MergeRequestApproversClient()
        assert m.user_search_check_and_log([{"id": 4}], None, [1, 2, 3]) == [1, 2, 3]

    @staticmethod
    def test_user_search_check_and_log_empty_approver_ids_gets_init():
        m = mra.MergeRequestApproversClient()
        assert m.user_search_check_and_log([{"id": 4}], {'email': "a@abc.com"}, None) == [4]
