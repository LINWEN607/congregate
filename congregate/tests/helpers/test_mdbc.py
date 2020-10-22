import unittest
import json
import pytest
from mock import patch, PropertyMock, MagicMock, mock_open
import warnings
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock

from congregate.helpers.mdbc import MongoConnector

@pytest.mark.unit_test
class MongoConnectorTests(unittest.TestCase):
    def setUp(self):
        self.c = MongoConnector(client=mongomock.MongoClient)

    def test_init(self):
        expected = ["projects", "groups", "users"]

        self.assertListEqual(self.c.db.list_collection_names(), expected)

    def test_insert_duplicate_data(self):
        data = {
            "id": 1,
            "hello": "world"
        }
        self.c.insert_data("users", data)
        self.c.insert_data("users", data)

        actual_number_of_documents = self.c.db.users.count_documents({})

        self.assertEqual(actual_number_of_documents, 1)
    
    def test_wildcard_collection_query(self):
        data = {
            "id": 1,
            "hello": "world"
        }
        self.c.insert_data("test-1", data)
        self.c.insert_data("test-2", data)

        actual = self.c.wildcard_collection_query("test")
        expected = ["test-1", "test-2"]

        self.assertListEqual(expected, actual)