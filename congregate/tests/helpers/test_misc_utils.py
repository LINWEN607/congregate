from datetime import datetime, timedelta
import base64
import unittest
from unittest import mock
from pytest import mark
import congregate.helpers.misc_utils as misc


@mark.unit_test
class MiscUtilsTests(unittest.TestCase):
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
            "-:: This.is-how/WE do\n&it#? - šđžčć") == "This.is-how WE do it - šđžčć"

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

    def test_pretty_print_key(self):
        self.assertEqual("Hello World How Are You",
                         misc.pretty_print_key("hello_world_how_are_you"))

    def test_strip_netloc(self):
        self.assertEqual("test.gitlab.com", misc.strip_netloc(
            "https://test.gitlab.com"))

    def test_strip_scheme(self):
        self.assertEqual("http", misc.strip_scheme("http://test.gitlab.com"))

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

    def test_do_yml_sub_simple_pattern(self):
        yml_file = "replace notreplace replace replacenot"
        subs = misc.do_yml_sub(
            yml_file, "replace ", "REPLACED")
        self.assertEqual(subs[1], 3)
        self.assertEqual(
            subs[0], "REPLACEDnotREPLACEDREPLACEDreplacenot"
        )

    def test_do_yml_sub_complex_pattern(self):
        yml_file = "I am the very model of a scientist Solarian, I've studied species Turian, Asari, and Batarian,"
        subs = misc.do_yml_sub(
            yml_file, "([A-Z])\\w+", "SPECIES")
        self.assertEqual(subs[1], 4)
        self.assertEqual(
            subs[0], "I am the very model of a scientist SPECIES, I've studied species SPECIES, SPECIES, and SPECIES,"
        )
