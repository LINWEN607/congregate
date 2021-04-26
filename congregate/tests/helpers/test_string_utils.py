import unittest
from unittest import mock
from pytest import mark
from congregate.helpers import string_utils

@mark.unit_test
class StringUtilsTests(unittest.TestCase):
    
    def test_strip_numbers(self):
        stripped = string_utils.strip_numbers("aaa98bbb98hhh222133")
        self.assertEqual(stripped, "aaabbbhhh")

    def test_strip_numbers_returns_empty(self):
        stripped = string_utils.strip_numbers("12345")
        self.assertEqual(stripped, "")

    def test_strip_numbers_returns_string_on_no_numbers(self):
        stripped = string_utils.strip_numbers("ABCD")
        self.assertEqual(stripped, "ABCD")

    def test_convert_single_space_to_underscore(self):
        expected = "hello_world"
        actual = string_utils.convert_to_underscores("hello world")

        self.assertEqual(expected, actual)

    def test_convert_multiple_spaces_to_underscore(self):
        expected = "replacing_spaces_with_underscores_in_a_sentence"
        actual = string_utils.convert_to_underscores(
            "replacing spaces with underscores in a sentence")

        self.assertEqual(expected, actual)

    def test_convert_multiple_slashes_to_underscore(self):
        expected = "absolute_path_to_file"
        actual = string_utils.convert_to_underscores("absolute/path/to/file")

        self.assertEqual(expected, actual)

    def test_clean_split(self):
        test_string = "/path/to/file"
        expected = ["path", "to", "file"]
        actual = string_utils.clean_split(test_string, "/")

        self.assertListEqual(expected, actual)
    
    @mock.patch("getpass.getpass")
    def test_obfuscate(self, secret):
        secret.return_value = "test"
        self.assertEqual(string_utils.obfuscate("Enter secret: "), "dGVzdA==")

    def test_deobfuscate(self):
        self.assertEqual(string_utils.deobfuscate("dGVzdA=="), "test")

    def test_deobfuscate_failed(self):
        with self.assertRaises(SystemExit):
            string_utils.deobfuscate("ddddGVzdA==")