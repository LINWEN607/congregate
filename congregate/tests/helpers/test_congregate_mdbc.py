import unittest
import warnings
from unittest.mock import patch, PropertyMock, mock_open
from pytest import mark
# mongomock is using deprecated logic as of Python 3.3
# This warning suppression is used so tests can pass
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import mongomock

from congregate.helpers.congregate_mdbc import CongregateMongoConnector


@mark.unit_test
class MongoConnectorTests(unittest.TestCase):
    def setUp(self):
        with patch("congregate.helpers.conf.Config.list_ci_source_config") as mock_list_ci_sources:
            mock_list_ci_sources.side_effect = [{}, {}]
            with patch("congregate.helpers.conf.Config.source_host", new_callable=PropertyMock) as mock_source_host:
                mock_source_host.return_value = "http://github.example.com"
                self.c = CongregateMongoConnector(client=mongomock.MongoClient)

    def test_init(self):
        expected = ["projects-github.example.com",
                    "groups-github.example.com", "users-github.example.com", "keys-github.example.com"]
        self.assertListEqual(self.c.db.list_collection_names(), expected)

    def test_find_user_email(self):
        data = {
            "id": 1,
            "email": "jdoe@email.com",
            "username": "jdoe"
        }
        self.c.insert_data("users-github.example.com", data)

        actual = self.c.find_user_email("jdoe")
        expected = "jdoe@email.com"

        self.assertEqual(expected, actual)
