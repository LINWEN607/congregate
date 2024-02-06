import unittest
from unittest import mock
from pytest import mark
from congregate.helpers.package_utils import *


@mark.unit_test
class PackageUtilsTests(unittest.TestCase):
    def test_pkg_info(self):
        with open("congregate/tests/data/pkg-info.example", 'r') as f:
            pkg_info = f.read()
        
        expected_metadata = {
            "author": "John Doe",
            "author_email": "jdoe@example.com",
            "classifier": "Programming Language :: Python :: 3.12",
            "description_content_type": "text/markdown",
            "home_page": "https://gitlab.com/",
            "license": "MIT",
            "metadata_version": "2.1",
            "name": "sample_package",
            "requires_dist": "xlsxwriter (>=3.1.2,<4.0.0)",
            "requires_python": ">=3.8.0",
            "summary": "A sample Python Project",
            "version": "0.1.0"
        }
        actual_metadata, _ = extract_pypi_package_metadata(pkg_info)

        self.assertDictEqual(actual_metadata, expected_metadata)
