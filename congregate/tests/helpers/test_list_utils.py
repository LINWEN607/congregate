import unittest
from pytest import mark
import congregate.helpers.list_utils as lutils


@mark.unit_test
class ListUtilsTests(unittest.TestCase):
    def test_remove_dupes_no_dupes(self):
        L = [{'id': 1, 'name': 'john', 'age': 34}, {'id': 2, 'name': 'jack',
                                                    'age': 34}, {'id': 3, 'name': 'hanna', 'age': 30}]
        de_duped = lutils.remove_dupes(L)
        self.assertEqual(de_duped, L)

    def test_remove_dupes_with_dupes(self):
        L = [{'id': 1, 'name': 'john', 'age': 34}, {'id': 1, 'name': 'john', 'age': 34}, {'id': 2, 'name': 'jack', 'age': 34}, {
            'id': 2, 'name': 'jack', 'age': 34}, {'id': 3, 'name': 'hanna', 'age': 30}, {'id': 3, 'name': 'hanna', 'age': 30}]
        de_duped = lutils.remove_dupes(L)
        self.assertEqual(de_duped, [{'id': 1, 'name': 'john', 'age': 34}, {
            'id': 2, 'name': 'jack', 'age': 34}, {'id': 3, 'name': 'hanna', 'age': 30}])

    def test_remove_dupes_with_empty_returns_empty(self):
        de_duped = lutils.remove_dupes([])
        self.assertEqual(de_duped, [])

    def test_remove_dupes_with_all_dupes_returns_single(self):
        L = [{'id': 1, 'name': 'john', 'age': 34}, {
            'id': 1, 'name': 'john', 'age': 34}, {'id': 1, 'name': 'john', 'age': 34}]
        de_duped = lutils.remove_dupes(L)
        self.assertEqual(de_duped, [{'id': 1, 'name': 'john', 'age': 34}])

    def test_safe_list_index_lookup(self):
        test = ["hello", "world"]
        expected = 0
        actual = lutils.safe_list_index_lookup(test, "hello")

        self.assertEqual(expected, actual)

    def test_safe_list_index_lookup_missing_index(self):
        self.assertIsNone(lutils.safe_list_index_lookup([], "hello"))
    
    def test_remove_dupes_with_keys(self):
        L = [
            {
                "id": 1,
                "path": "test-path",
                "test": "test"
            },
            {
                "id": 1,
                "path": "test-path2",
                "test": "test"
            },
            {
                "id": 1,
                "path": "test-path",
                "test": "test"
            },
            {
                "id": 2,
                "path": "test-path2",
                "test": "test"
            }
        ]

        expected = [
            {
                "id": 1,
                "path": "test-path",
                "test": "test"
            },
            {
                "id": 1,
                "path": "test-path2",
                "test": "test"
            },
            {
                "id": 2,
                "path": "test-path2",
                "test": "test"
            }
        ]
        actual = lutils.remove_dupes_with_keys(L, ["id", "path"])
        self.assertEqual(expected, actual)