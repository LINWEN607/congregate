from datetime import datetime, timedelta
import base64
import unittest
from unittest import mock
from pytest import mark
from congregate.tests.mockapi.jenkins.jobs import JenkinsJobsApi
import congregate.helpers.misc_utils as misc


@mark.unit_test
class MiscUtilsTests(unittest.TestCase):
    def test_remove_dupes_no_dupes(self):
        L = [{'id': 1, 'name': 'john', 'age': 34}, {'id': 2, 'name': 'jack',
                                                    'age': 34}, {'id': 3, 'name': 'hanna', 'age': 30}]
        de_duped = misc.remove_dupes(L)
        self.assertEqual(de_duped, L)

    def test_remove_dupes_with_dupes(self):
        L = [{'id': 1, 'name': 'john', 'age': 34}, {'id': 1, 'name': 'john', 'age': 34}, {'id': 2, 'name': 'jack', 'age': 34}, {
            'id': 2, 'name': 'jack', 'age': 34}, {'id': 3, 'name': 'hanna', 'age': 30}, {'id': 3, 'name': 'hanna', 'age': 30}]
        de_duped = misc.remove_dupes(L)
        self.assertEqual(de_duped, [{'id': 1, 'name': 'john', 'age': 34}, {
            'id': 2, 'name': 'jack', 'age': 34}, {'id': 3, 'name': 'hanna', 'age': 30}])

    def test_remove_dupes_with_empty_returns_empty(self):
        de_duped = misc.remove_dupes([])
        self.assertEqual(de_duped, [])

    def test_remove_dupes_with_all_dupes_returns_single(self):
        L = [{'id': 1, 'name': 'john', 'age': 34}, {
            'id': 1, 'name': 'john', 'age': 34}, {'id': 1, 'name': 'john', 'age': 34}]
        de_duped = misc.remove_dupes(L)
        self.assertEqual(de_duped, [{'id': 1, 'name': 'john', 'age': 34}])

    def test_remove_dupes_but_take_higher_access(self):
        test = [
            {
                "id": 1,
                "access_level": 10
            },
            {
                "id": 1,
                "access_level": 50
            },
            {
                "id": 1,
                "access_level": 20
            },
            {
                "id": 2,
                "access_level": 10
            },
            {
                "id": 2,
                "access_level": 40
            },
            {
                "id": 3,
                "access_level": 20
            }
        ]
        expected = [
            {
                "id": 1,
                "access_level": 50,
                "index": 0
            },
            {
                "id": 2,
                "access_level": 40,
                "index": 1
            },
            {
                "id": 3,
                "access_level": 20
            }
        ]
        actual = misc.remove_dupes_but_take_higher_access(test)
        self.assertEqual(expected, actual)

    def test_remove_dupes_with_keys(self):
        L = [
            {
                "id": 1,
                "path": "test-path",
                "test": "test"
            },
            {
                "id": 1,
                "path": "test-path2",
                "test": "test"
            },
            {
                "id": 1,
                "path": "test-path",
                "test": "test"
            },
            {
                "id": 2,
                "path": "test-path2",
                "test": "test"
            }
        ]

        expected = [
            {
                "id": 1,
                "path": "test-path",
                "test": "test"
            },
            {
                "id": 1,
                "path": "test-path2",
                "test": "test"
            },
            {
                "id": 2,
                "path": "test-path2",
                "test": "test"
            }
        ]
        actual = misc.remove_dupes_with_keys(L, ["id", "path"])
        self.assertEqual(expected, actual)

    def test_parse_query_params(self):
        qp = misc.parse_query_params({"abc": 1})
        self.assertEqual(qp, "?abc=1")

    def test_parse_query_params_on_empty(self):
        qp = misc.parse_query_params({})
        self.assertEqual(qp, "")

    def test_parse_query_params_on_none(self):
        qp = misc.parse_query_params({"abc": None})
        self.assertEqual(qp, "")

    def test_get_dry_log(self):
        assert misc.get_dry_log() == "DRY-RUN: "
        assert misc.get_dry_log(False) == ""
        assert misc.get_dry_log("whatever") == "DRY-RUN: "

    def test_get_rollback_log(self):
        assert misc.get_rollback_log() == ""
        assert misc.get_rollback_log(True) == "Rollback: "
        assert misc.get_rollback_log("whatever") == "Rollback: "

    

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

        self.assertEqual(expected, misc.rewrite_json_list_into_dict(initial))

    def test_get_timedelta_older_than_twenty_four_hours(self):
        timestamp = "2020-03-10T17:09:32.322Z"
        assert misc.get_timedelta(timestamp) > 24

    def test_get_timedelta_older_than_twenty_four_hours_different_format(self):
        timestamp = "2013-09-30T13:46:02Z"
        assert misc.get_timedelta(timestamp) > 24

    def test_get_timedelta_newer_than_twenty_four_hours(self):
        timestamp = str(datetime.now()).replace(" ", "T")
        assert misc.get_timedelta(timestamp) < 24

    def test_get_timedelta_exactly_twenty_four_hours(self):
        timestamp = str(datetime.today() - timedelta(days=1)).replace(" ", "T")
        assert misc.get_timedelta(timestamp) == 24

    def test_validate_name(self):
        assert misc.validate_name(
            "-:: This.is-how/WE do\n&it") == "This.is-how WE do it"

    @mock.patch("requests.Response")
    def test_safe_json_response_with_exception(self, response):
        response.json.side_effect = [ValueError]
        expected = None
        actual = misc.safe_json_response(response)

        self.assertEqual(expected, actual)

    @mock.patch("requests.Response")
    def test_safe_json_response_without_exception(self, response):
        response.json.side_effect = [{"hello": "world"}]
        expected = {"hello": "world"}
        actual = misc.safe_json_response(response)

        self.assertEqual(expected, actual)

    def test_safe_json_response_with_none(self):
        self.assertIsNone(misc.safe_json_response(None))

    def test_safe_list_index_lookup(self):
        test = ["hello", "world"]
        expected = 0
        actual = misc.safe_list_index_lookup(test, "hello")

        self.assertEqual(expected, actual)

    def test_safe_list_index_lookup_missing_index(self):
        self.assertIsNone(misc.safe_list_index_lookup([], "hello"))

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

        actual = misc.xml_to_dict(test_xml)

        self.assertEqual(expected, actual)

    def test_xml_to_dict_complex(self):
        j = JenkinsJobsApi()
        test_xml = j.get_test_job_config_xml()
        expected = j.get_job_config_dict()

        actual = misc.xml_to_dict(test_xml)

        self.assertEqual(expected, actual)


    def test_get_hash_of_dict(self):
        expected = "97abd2c1280faf011ac57adcf2bcad8a180e5a08"
        actual = misc.get_hash_of_dict({"Hello": "world"})

        self.assertEqual(expected, actual)

    def test_get_duplicate_paths_projects(self):
        data = [{
            "path_with_namespace": "a/b"
        },
            {
            "path_with_namespace": "d/b"
        },
            {
            "path_with_namespace": "d/b"
        },
            {
            "path_with_namespace": "d/b"
        },
            {
            "path_with_namespace": "a/b"
        },
            {
            "path_with_namespace": "b/c"
        }]
        expected = ["a/b", "d/b"]
        actual = misc.get_duplicate_paths(data)

        self.assertEqual(expected, actual)

    def test_get_duplicate_paths_groupss(self):
        data = [{
            "full_path": "a/b"
        },
            {
            "full_path": "d/b"
        },
            {
            "full_path": "d/b"
        },
            {
            "full_path": "d/b"
        },
            {
            "full_path": "a/b"
        },
            {
            "full_path": "b/c"
        }]
        expected = ["a/b", "d/b"]
        actual = misc.get_duplicate_paths(data, are_projects=False)

        self.assertEqual(expected, actual)

    def test_dig_found(self):
        test = {
            "nest": {
                "hello": {
                    "world": "this is nested"
                }
            }
        }

        expected = "this is nested"
        actual = misc.dig(test, "nest", "hello", "world")

        self.assertEqual(expected, actual)

    def test_dig_not_found(self):
        test = {
            "nest": {
                "hello": {
                    "world": "this is nested"
                }
            }
        }

        actual = misc.dig(test, "nest", "hello", "not found")

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
        actual = misc.dig(test, "nest", "hello")

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
        actual = misc.dig(test, "nest", "key", default=[])

        self.assertEqual(expected, actual)

    def test_pretty_print_key(self):
        expected = "Hello World How Are You"
        actual = misc.pretty_print_key("hello_world_how_are_you")

        self.assertEqual(expected, actual)

    def test_strip_protocol(self):
        expected = "test.gitlab.com"
        actual = misc.strip_protocol("https://test.gitlab.com")
        self.assertEqual(expected, actual)

    def test_pop_multiple_keys(self):
        src = {
            "id": 1,
            "name": "name",
            "path": "path"
        }
        self.assertEqual({"path": "path"},
                         misc.pop_multiple_keys(src, ["id", "name"]))
        self.assertEqual(src, misc.pop_multiple_keys(src, ["ids", "names"]))

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

        for k, v in misc.sort_dict(test_dict).items():
            self.assertEqual(expected[k], v)

    class MockResponse():
        def __init__(self):
            self.content = ""
            self.status_code = 200

        def json(self):
            return {"content": self.content}

    def test_get_b64decode_content_from_response(self):
        mr = self.MockResponse()
        mr.content = base64.b64encode(b'test')
        a = misc.get_decoded_string_from_b64_response_content(mr)
        self.assertEqual(a, "test")

    def test_do_yml_sub(self):
        subs = misc.do_yml_sub(
            "This has to REPLACE in several REPLACE place", "REPLACE", "REPLACED")
        self.assertEqual(subs[1], 2)
        self.assertEqual(
            subs[0], "This has to REPLACED in several REPLACED place"
        )
