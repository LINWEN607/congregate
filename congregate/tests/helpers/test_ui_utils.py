import unittest
from unittest import mock
from pytest import mark
import congregate.helpers.ui_utils as ui


@mark.unit_test
class UiUtilsTests(unittest.TestCase):
    @mock.patch("congregate.helpers.ui_utils.open",
                new=mock.mock_open(read_data=b"abc123"))
    @mock.patch("congregate.helpers.ui_utils.get_hash_of_dirs")
    def test_is_ui_out_of_date_false(self, mock_hash):
        mock_hash.return_value = b"abc123"
        expected = False
        actual = ui.is_ui_out_of_date("")

        self.assertEqual(expected, actual)

    @mock.patch('builtins.open', new=mock.mock_open(read_data=b"abc123"))
    @mock.patch("congregate.helpers.ui_utils.get_hash_of_dirs")
    def test_is_ui_out_of_date_true(self, mock_hash):
        mock_hash.return_value = b"def456"
        expected = True
        actual = ui.is_ui_out_of_date("")

        self.assertEqual(expected, actual)

    @mock.patch("congregate.helpers.ui_utils.open")
    @mock.patch("congregate.helpers.file_utils.get_hash_of_dirs")
    def test_is_ui_out_of_date_true_with_exception(self, mock_hash, mock_open):
        mock_open.side_effect = [IOError]
        mock_hash.return_value = b"abc123"
        expected = True
        actual = ui.is_ui_out_of_date("")

        self.assertEqual(expected, actual)
