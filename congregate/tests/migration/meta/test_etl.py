import unittest
import pytest
import pandas as pd
from mock import patch
from congregate.migration.meta.etl import WaveSpreadsheetHandler as wh

@pytest.mark.unit_test
class WaveSpreadsheetHandlerTests(unittest.TestCase):
    def test_handle_excel_file(self):
        expected = "excel"
        actual = wh("./test_excel.xlsx")
        self.assertEqual(expected, actual.file_type)

    def test_handle_csv_file(self):
        expected = "csv"
        actual = wh("./test_csv.csv")
        self.assertEqual(expected, actual.file_type)
    
    def test_handle_invalid_file(self):
        with self.assertRaises(ValueError):
            wh("./test_invalid.html")
    
    @patch("pandas.read_excel")
    def test_handle_excel_file_read(self, read_excel):
        expected = pd.DataFrame(
            {
                "Wave name": {
                    "0": "Wave 1",
                    "1": "Wave 1"
                },
                "not needed": {
                    "0": "asdflkasjdf",
                    "1": "asdflkasjdf"
                },
                "not needed_2": {
                    "0": 123,
                    "1": 124
                },
                "Wave date": {
                    "0": 1609459200000,
                    "1": 1609459200000
                },
                "notneeded3": {
                    "0": -1,
                    "1": 0
                },
                "notneeded4": {
                    "0": "qqq",
                    "1": "qqq"
                },
                "Source Url": {
                    "0": "test.git",
                    "1": "test.git"
                }
            }
        )
        read_excel.return_value = expected
        actual = wh("./test_excel.xlsx").read_file_as_dataframe()
        # self.assertEqual(expected, actual)
        pd.testing.assert_frame_equal(expected, actual)
    
    @patch("pandas.read_excel")
    def test_handle_excel_file_read_only_include_specific_column(self, read_excel):
        read_excel.return_value = pd.DataFrame(
            {
                "Wave name": {
                    "0": "Wave 1",
                    "1": "Wave 1"
                },
                "not needed": {
                    "0": "asdflkasjdf",
                    "1": "asdflkasjdf"
                },
                "not needed_2": {
                    "0": 123,
                    "1": 124
                },
                "Wave date": {
                    "0": 1609459200000,
                    "1": 1609459200000
                },
                "notneeded3": {
                    "0": -1,
                    "1": 0
                },
                "notneeded4": {
                    "0": "qqq",
                    "1": "qqq"
                },
                "Source Url": {
                    "0": "test.git",
                    "1": "test.git"
                }
            }
        )
        expected = pd.DataFrame(
            {
                "Wave name": {
                    "0": "Wave 1",
                    "1": "Wave 1"
                }
            }
        )
        actual = wh("./test_excel.xlsx", columns_to_use=['Wave name']).read_file_as_dataframe()
        # self.assertEqual(expected, actual)
        pd.testing.assert_frame_equal(expected, actual)

    @patch("pandas.read_csv")
    def test_handle_csv_file_read(self, read_csv):
        expected = pd.DataFrame(
            {
                "Wave name": {
                    "0": "Wave 1",
                    "1": "Wave 1"
                },
                "not needed": {
                    "0": "asdflkasjdf",
                    "1": "asdflkasjdf"
                },
                "not needed_2": {
                    "0": 123,
                    "1": 124
                },
                "Wave date": {
                    "0": 1609459200000,
                    "1": 1609459200000
                },
                "notneeded3": {
                    "0": -1,
                    "1": 0
                },
                "notneeded4": {
                    "0": "qqq",
                    "1": "qqq"
                },
                "Source Url": {
                    "0": "test.git",
                    "1": "test.git"
                }
            }
        )
        read_csv.return_value = expected
        actual = wh("./test_csv.csv").read_file_as_dataframe()
        # self.assertEqual(expected, actual)
        pd.testing.assert_frame_equal(expected, actual)

    @patch("pandas.read_csv")
    def test_handle_csv_file_read_only_include_specific_column(self, read_csv):
        read_csv.return_value = pd.DataFrame(
            {
                "Wave name": {
                    "0": "Wave 1",
                    "1": "Wave 1"
                },
                "not needed": {
                    "0": "asdflkasjdf",
                    "1": "asdflkasjdf"
                },
                "not needed_2": {
                    "0": 123,
                    "1": 124
                },
                "Wave date": {
                    "0": 1609459200000,
                    "1": 1609459200000
                },
                "notneeded3": {
                    "0": -1,
                    "1": 0
                },
                "notneeded4": {
                    "0": "qqq",
                    "1": "qqq"
                },
                "Source Url": {
                    "0": "test.git",
                    "1": "test.git"
                }
            }
        )
        expected = pd.DataFrame(
            {
                "Wave name": {
                    "0": "Wave 1",
                    "1": "Wave 1"
                }
            }
        )
        actual = wh("./test_csv.csv", columns_to_use=['Wave name']).read_file_as_dataframe()
        pd.testing.assert_frame_equal(expected, actual)

    @patch("pandas.read_csv")
    def test_handle_csv_file_read_as_json(self, read_csv):
        read_csv.return_value = pd.DataFrame(
            {
                "Wave name": {
                    "0": "Wave 1",
                    "1": "Wave 1"
                },
                "not needed": {
                    "0": "asdflkasjdf",
                    "1": "asdflkasjdf"
                },
                "not needed_2": {
                    "0": 123,
                    "1": 124
                },
                "Wave date": {
                    "0": 1609459200000,
                    "1": 1609459200000
                },
                "notneeded3": {
                    "0": -1,
                    "1": 0
                },
                "notneeded4": {
                    "0": "qqq",
                    "1": "qqq"
                },
                "Source Url": {
                    "0": "test.git",
                    "1": "test.git"
                }
            }
        )
        expected = [
            {
                "Wave name": "Wave 1",
                "not needed": "asdflkasjdf",
                "not needed_2": 123,
                "Wave date": 1609459200000,
                "notneeded3": -1,
                "notneeded4": "qqq",
                "Source Url": "test.git"
            },
            {
                "Wave name": "Wave 1",
                "not needed": "asdflkasjdf",
                "not needed_2": 124,
                "Wave date": 1609459200000,
                "notneeded3": 0,
                "notneeded4": "qqq",
                "Source Url": "test.git"
            }
        ]
        actual = wh("./test_csv.csv").read_file_as_json()
        for i, _ in enumerate(expected):
            self.assertDictEqual(
                actual[i], expected[i])