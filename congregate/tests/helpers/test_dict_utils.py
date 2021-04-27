import unittest
from unittest import mock
from pytest import mark
import congregate.helpers.dict_utils as dutils


@mark.unit_test
class DictUtilsTests(unittest.TestCase):
    def test_pop_multiple_keys(self):
        src = {
            "id": 1,
            "name": "name",
            "path": "path"
        }
        self.assertEqual({"path": "path"},
                         dutils.pop_multiple_keys(src, ["id", "name"]))
        self.assertEqual(src, dutils.pop_multiple_keys(src, ["ids", "names"]))

    def test_dig_found(self):
        test = {
            "nest": {
                "hello": {
                    "world": "this is nested"
                }
            }
        }

        expected = "this is nested"
        actual = dutils.dig(test, "nest", "hello", "world")

        self.assertEqual(expected, actual)

    def test_dig_not_found(self):
        test = {
            "nest": {
                "hello": {
                    "world": "this is nested"
                }
            }
        }

        actual = dutils.dig(test, "nest", "hello", "not found")

        self.assertIsNone(actual)

    def test_dig_return_dict(self):
        test = {
            "nest": {
                "hello": {
                    "world": "this is nested"
                }
            }
        }

        expected = {
            "world": "this is nested"
        }
        actual = dutils.dig(test, "nest", "hello")

        self.assertEqual(expected, actual)

    def test_dig_return_different_default(self):
        test = {
            "nest": {
                "hello": {
                    "world": "this is nested"
                }
            }
        }
        expected = []
        actual = dutils.dig(test, "nest", "key", default=[])

        self.assertEqual(expected, actual)

    def test_sort_dict(self):
        test_dict = {
            "b": 0,
            "e": 5,
            "a": 7
        }

        expected = {
            "a": 7,
            "b": 0,
            "e": 5
        }

        for k, v in dutils.sort_dict(test_dict).items():
            self.assertEqual(expected[k], v)

    def test_xml_to_dict_simple(self):
        test_xml = """
        <test>
            <tag>true</tag>
            <other-tag>a string</other-tag>
            <another-tag>false</another-tag>
        </test>
        """
        expected = {
            "test": {
                "tag": True,
                "other-tag": "a string",
                "another-tag": False
            }
        }

        actual = dutils.xml_to_dict(test_xml)

        self.assertEqual(expected, actual)


    def test_get_hash_of_dict(self):
        expected = "97abd2c1280faf011ac57adcf2bcad8a180e5a08"
        actual = dutils.get_hash_of_dict({"Hello": "world"})

        self.assertEqual(expected, actual)

    def test_rewrite_json_list_into_dict(self):
        initial = [
            {
                "hello": {
                    "world": "how are you"
                }
            },
            {
                "world": {
                    "this": "is another test"
                }
            }
        ]
        expected = {
            "hello": {
                "world": "how are you"
            },
            "world": {
                "this": "is another test"
            }
        }

        self.assertEqual(expected, dutils.rewrite_json_list_into_dict(initial))