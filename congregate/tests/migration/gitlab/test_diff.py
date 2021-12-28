import unittest
from pytest import mark
from gitlab_ps_utils.jsondiff import Comparator


@mark.unit_test
class ComparatorTests(unittest.TestCase):
    def setUp(self):
        self.engine = Comparator()

    def test_list_comparison(self):
        list_one = [{"Hello": "World"}, 2, 3, 4, 5]
        list_two = [5, 4, 3, 2, {"Hello": "World"}, 0]

        expected = {0: {u'+++': 0}}
        actual = self.engine._compare_arrays(list_one, list_two)

        self.assertEqual(expected, actual)


    def test_list_comparison_long_list(self):
        list_one = [{"Hello": "World"}, 2, 3, 4, 5]
        list_two = [5, 4, 3, 2, {"Hello": "World"}, 0, 10, 15]

        expected = {0: {u'+++': 0}, 1: {u'+++': 10}, 2: {u'+++': 15}}
        actual = self.engine._compare_arrays(list_one, list_two)

        self.assertEqual(expected, actual)
