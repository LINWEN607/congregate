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
        with patch("congregate.helpers.conf.Config.list_ci_source_config") as mock_list_ci_sources:
            mock_list_ci_sources.side_effect = [{}, {}]
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
    
    def test_insert_tuple(self):
        data = ({
            "id": 1,
            "hello": "world"
        }, True)
        self.c.insert_data("users", data)

        actual = self.c.db['users'].find_one()
        actual.pop("_id")
        expected = {
            "id": 1,
            "hello": "world"
        }

        self.assertDictEqual(expected, actual)
    
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
    
    def test_stream_collection(self):
        data = [{
            "id": 1,
            "email": "jdoe@email.com",
            "username": "jdoe"
        }, {
            "id": 2,
            "email": "jdoe2@email.com",
            "username": "jdoe2"
        }]
        for d in data:
            self.c.insert_data("users", d)
            d.pop("_id")
        
        actual = []
        for u, _ in self.c.stream_collection("users"):
            actual.append(u)

        self.assertListEqual(data, actual)


    def test_find_user_email(self):
        data = {
            "id": 1,
            "email": "jdoe@email.com",
            "username": "jdoe"
        }
        self.c.insert_data("users", data)

        actual = self.c.find_user_email("jdoe")
        expected = "jdoe@email.com"

        self.assertEqual(expected, actual)

    @patch('builtins.open', new=mock_open(read_data=b'[{"id": 1,"hello": "world"}]'))
    @patch("congregate.helpers.misc_utils.read_json_file_into_object")
    def test_insert_json_file_into_mongo(self, json_file):
        json_file.return_value = [{
            "id": 1,
            "hello": "world"
        }]
        self.c.ingest_json_file_into_mongo("/path/to/test.json")

        actual = self.c.db['test'].find_one()
        actual.pop("_id")
        expected = {
            "id": 1,
            "hello": "world"
        }

        self.assertDictEqual(expected, actual)

    @patch('builtins.open', new=mock_open(read_data=b'[{"id": 1,"hello": "world"}]'))
    @patch("congregate.helpers.misc_utils.read_json_file_into_object")
    def test_insert_json_file_into_mongo_with_collection(self, json_file):
        json_file.return_value = [{
            "id": 1,
            "hello": "world"
        }]
        self.c.ingest_json_file_into_mongo("/path/to/test.json", "coll")

        actual = self.c.db['coll'].find_one()
        actual.pop("_id")
        expected = {
            "id": 1,
            "hello": "world"
        }

        self.assertDictEqual(expected, actual)

    @patch('builtins.open', new=mock_open(read_data=b'[{"id": 1,"hello": "world"}]'))
    @patch("congregate.helpers.misc_utils.read_json_file_into_object")
    @patch("congregate.helpers.misc_utils.find_files_in_folder")
    @patch("os.listdir")
    def test_re_ingest_into_mongo(self, mock_list_dir, mock_find, json_file):
        mock_list_dir.return_value = ["projects.json", "groups.json", "teamcity-0.json", "teamcity-1.json", "test.json"]
        mock_find.return_value = ["test.json"]
        json_file.return_value = [{
            "id": 1,
            "hello": "world"
        }]
        self.c.re_ingest_into_mongo("test")

        actual = self.c.db['test'].find_one()
        actual.pop("_id")
        expected = {
            "id": 1,
            "hello": "world"
        }

        self.assertDictEqual(expected, actual)


        