import unittest
import warnings
from unittest.mock import patch, PropertyMock, mock_open
from pytest import mark
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock

from congregate.helpers.mdbc import MongoConnector


@mark.unit_test
class MongoConnectorTests(unittest.TestCase):
    def setUp(self):
        with patch("congregate.helpers.conf.Config.list_ci_source_config") as mock_list_ci_sources:
            mock_list_ci_sources.side_effect = [{}, {}]
            with patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock) as mock_source_host:
                mock_source_host.return_value = "http://github.example.com"
                self.c = MongoConnector(
                    db='test', client=mongomock.MongoClient)

    def test_insert_duplicate_data(self):
        data = {
            "id": 1,
            "hello": "world"
        }
        self.c.insert_data("sample", data)
        self.c.insert_data("sample", data)

        actual_number_of_documents = self.c.db.sample.count_documents({})

        self.assertEqual(actual_number_of_documents, 1)

    def test_insert_tuple(self):
        data = ({
            "id": 1,
            "hello": "world"
        }, True)
        self.c.insert_data("sample", data)

        actual = self.c.db['sample'].find_one()
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

    @patch('builtins.open',
           new=mock_open(read_data=b'[{"id": 1,"hello": "world"}]'))
    @patch("gitlab_ps_utils.json_utils.read_json_file_into_object")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    def test_insert_json_file_into_mongo(self, mock_source_host, json_file):
        mock_source_host.return_value = "http://gitlab.example.com"
        json_file.return_value = [{
            "id": 1,
            "hello": "world"
        }]
        self.c.ingest_json_file_into_mongo("/path/to/test.json")

        actual = self.c.db['test-gitlab.example.com'].find_one()
        actual.pop("_id")
        expected = {
            "id": 1,
            "hello": "world"
        }

        self.assertDictEqual(expected, actual)

    @patch('builtins.open',
           new=mock_open(read_data=b'[{"id": 1,"hello": "world"}]'))
    @patch("gitlab_ps_utils.json_utils.read_json_file_into_object")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    def test_insert_json_file_into_mongo_with_collection(self, mock_source_host, json_file):
        mock_source_host.return_value = "http://gitlab.example.com"
        json_file.return_value = [{
            "id": 1,
            "hello": "world"
        }]
        self.c.ingest_json_file_into_mongo("/path/to/test.json", "coll")

        actual = self.c.db['coll-gitlab.example.com'].find_one()
        actual.pop("_id")
        expected = {
            "id": 1,
            "hello": "world"
        }

        self.assertDictEqual(expected, actual)

    @patch('builtins.open',
           new=mock_open(read_data=b'[{"id": 1,"hello": "world"}]'))
    @patch("gitlab_ps_utils.json_utils.read_json_file_into_object")
    @patch("gitlab_ps_utils.file_utils.find_files_in_folder")
    @patch("os.listdir")
    @patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock)
    def test_re_ingest_into_mongo(self, mock_source_host, mock_list_dir, mock_find, json_file):
        mock_source_host.return_value = "http://gitlab.example.com"
        mock_list_dir.return_value = [
            "projects.json", "groups.json", "teamcity-0.json", "teamcity-1.json", "test.json"]
        mock_find.return_value = ["test.json"]
        json_file.return_value = [{
            "id": 1,
            "hello": "world"
        }]
        self.c.re_ingest_into_mongo("test")

        actual = self.c.db['test-gitlab.example.com'].find_one()
        actual.pop("_id")
        expected = {
            "id": 1,
            "hello": "world"
        }

        self.assertDictEqual(expected, actual)
