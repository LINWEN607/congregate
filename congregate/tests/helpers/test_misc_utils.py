from datetime import datetime, timedelta
import base64
import unittest
from unittest import mock
from pytest import mark
from congregate.tests.helpers.mock_data.results import MockProjectResults
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

    @mock.patch("congregate.helpers.misc_utils.__get_filename_from_cd")
    @mock.patch("congregate.helpers.misc_utils.__is_downloadable")
    @mock.patch("io.TextIOBase")
    @mock.patch("builtins.open")
    @mock.patch("requests.Response")
    @mock.patch("congregate.helpers.misc_utils.get")
    def test_download_file_sets_filename_from_response_headers_when_filename_none(self, g, resp, o, f, idl, fn):
        fn.return_value = "returned"
        idl.return_value = True
        resp.headers = {"Content-Disposition": "not_returned=returned"}
        o.return_value = f
        g.return_value = resp
        filename = misc.download_file("url", "path")
        self.assertEqual(filename, "returned")

    @mock.patch("congregate.helpers.misc_utils.__is_downloadable")
    @mock.patch("io.TextIOBase")
    @mock.patch("builtins.open")
    @mock.patch("requests.Response")
    @mock.patch("congregate.helpers.misc_utils.get")
    def test_download_file_uses_filename_from_param(self, g, resp, o, f, idl):
        idl.return_value = True
        resp.headers = {"Content-Disposition": "not_returned=returned"}
        o.return_value = f
        g.return_value = resp
        filename = misc.download_file("url", "path", filename="passed")
        self.assertEqual(filename, "passed")

    @mock.patch("os.path.exists")
    @mock.patch("os.makedirs")
    def test_create_local_project_export_structure(self, mock_make_dirs, mock_exists):
        mock_exists.return_value = False
        misc.create_local_project_export_structure("/a/b/c")
        mock_make_dirs.assert_called_with("/a/b/c")

    def test_strip_numbers(self):
        stripped = misc.strip_numbers("aaa98bbb98hhh222133")
        self.assertEqual(stripped, "aaabbbhhh")

    def test_strip_numbers_returns_empty(self):
        stripped = misc.strip_numbers("12345")
        self.assertEqual(stripped, "")

    def test_strip_numbers_returns_string_on_no_numbers(self):
        stripped = misc.strip_numbers("ABCD")
        self.assertEqual(stripped, "ABCD")

    def test_parse_query_params(self):
        qp = misc.parse_query_params({"abc": 1})
        self.assertEqual(qp, "?abc=1")

    def test_parse_query_params_on_empty(self):
        qp = misc.parse_query_params({})
        self.assertEqual(qp, "")

    def test_parse_query_params_on_none(self):
        qp = misc.parse_query_params({"abc": None})
        self.assertEqual(qp, "")

    @mock.patch("os.getenv")
    @mock.patch("os.getcwd")
    def test_get_congregate_path_with_no_env_set(self, get_cwd, get_env):
        get_env.return_value = None
        get_cwd.return_value = "FAKEPATH"
        app_path = misc.get_congregate_path()
        self.assertEqual(app_path, "FAKEPATH")

    @mock.patch("os.getenv")
    def test_get_congregate_path_with_env_set(self, get_env):
        get_env.return_value = "FAKEPATH"
        app_path = misc.get_congregate_path()
        self.assertEqual(app_path, "FAKEPATH")

    def test_get_dry_log(self):
        assert misc.get_dry_log() == "DRY-RUN: "
        assert misc.get_dry_log(False) == ""
        assert misc.get_dry_log("whatever") == "DRY-RUN: "

    def test_get_rollback_log(self):
        assert misc.get_rollback_log() == ""
        assert misc.get_rollback_log(True) == "Rollback: "
        assert misc.get_rollback_log("whatever") == "Rollback: "

    @mock.patch("getpass.getpass")
    def test_obfuscate(self, secret):
        secret.return_value = "test"
        self.assertEqual(misc.obfuscate("Enter secret: "), "dGVzdA==")

    def test_deobfuscate(self):
        self.assertEqual(misc.deobfuscate("dGVzdA=="), "test")

    def test_deobfuscate_failed(self):
        with self.assertRaises(SystemExit):
            misc.deobfuscate("ddddGVzdA==")

    @mock.patch("os.path.exists")
    def test_is_recent_file_no_file(self, exists):
        exists.return_value = False
        self.assertFalse(misc.is_recent_file("test"))

    @mock.patch("os.path.exists")
    @mock.patch("os.path.getsize")
    def test_is_recent_file_empty_file(self, size, exists):
        exists.return_value = True
        size.return_value = 0
        self.assertFalse(misc.is_recent_file("test"))

    @mock.patch("os.path.exists")
    @mock.patch("os.path.getsize")
    @mock.patch("os.path.getmtime")
    def test_is_recent_file_not_recent(self, mtime, size, exists):
        exists.return_value = True
        size.return_value = 1
        mtime.return_value = 0
        self.assertFalse(misc.is_recent_file("test"))

    @mock.patch("os.path.exists")
    @mock.patch("os.path.getsize")
    @mock.patch("os.path.getmtime")
    def test_is_recent_file(self, mtime, size, exists):
        exists.return_value = True
        size.return_value = 1
        mtime.return_value = 9999999999
        self.assertTrue(misc.is_recent_file("test"))

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

    def test_is_dot_com(self):
        assert misc.is_dot_com("asdasd") is False
        assert misc.is_dot_com("https://gitlab.com") is True

    def test_is_github_dot_com(self):
        assert misc.is_github_dot_com("asdasd") is False
        assert misc.is_github_dot_com("https://api.github.com") is True

    def test_check_is_project_or_group_for_logging_project(self):
        assert misc.check_is_project_or_group_for_logging(True) is "Project"
        assert misc.check_is_project_or_group_for_logging(False) is "Group"

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

    @mock.patch("congregate.helpers.misc_utils.read_json_file_into_object")
    @mock.patch("glob.glob")
    def test_stitch_json(self, glob, json):
        results = MockProjectResults()
        glob.return_value = [
            'project_migration_results_2020-05-05_22:17:45.335715.json',
            'project_migration_results_2020-05-05_21:38:04.565534.json',
            'project_migration_results_2020-05-05_21:17:42.719402.json',
            'project_migration_results_2020-05-05_19:26:18.616265.json',
            'project_migration_results_2020-04-28_23:06:02.139918.json'
        ]

        json.side_effect = [
            results.get_completely_failed_results(),
            results.get_partially_successful_results(),
            results.get_successful_results_subset()
        ]

        expected = results.get_completely_successful_results()
        actual = misc.stitch_json_results(steps=2)

        self.assertEqual(expected, actual)

    @mock.patch("congregate.helpers.misc_utils.read_json_file_into_object")
    @mock.patch("glob.glob")
    def test_stitch_json_too_many_steps(self, glob, json):
        results = MockProjectResults()
        glob.return_value = [
            'project_migration_results_2020-05-05_22:17:45.335715.json',
            'project_migration_results_2020-05-05_21:38:04.565534.json',
            'project_migration_results_2020-05-05_21:17:42.719402.json',
            'project_migration_results_2020-05-05_19:26:18.616265.json',
            'project_migration_results_2020-04-28_23:06:02.139918.json'
        ]

        json.side_effect = [
            results.get_completely_failed_results(),
            results.get_partially_successful_results(),
            results.get_successful_results_subset(),
            [],
            []
        ]

        expected = results.get_completely_successful_results()
        actual = misc.stitch_json_results(steps=6)

        self.assertEqual(expected, actual)

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



    @mock.patch("os.path.exists")
    def test_get_hash_of_dirs_no_dir(self, path):
        path.return_value = False
        expected = -1
        actual = misc.get_hash_of_dirs("")

        self.assertEqual(expected, actual)

    @mock.patch("os.path.exists")
    @mock.patch("os.walk")
    def test_get_hash_of_dirs_with_exception(self, walk, path):
        path.return_value = True
        walk.side_effect = [Exception]
        expected = -2
        actual = misc.get_hash_of_dirs("")

        self.assertEqual(expected, actual)

    @mock.patch("congregate.helpers.misc_utils.open", new=mock.mock_open(read_data=b"def456"))
    @mock.patch("os.path.exists")
    @mock.patch("os.walk")
    def test_get_hash_of_dirs_with_dir(self, walk, path):
        path.return_value = True
        walk.return_value = [
            ('/foo', ('bar',), ('baz',)),
            ('/foo/bar', (), ('spam', 'eggs')),
        ]
        expected = "b981b8d32b55cbddc5c192bed125dc5fe42eb922"
        actual = misc.get_hash_of_dirs("")

        self.assertEqual(expected, actual)

    @mock.patch("congregate.helpers.misc_utils.open")
    @mock.patch("os.path.exists")
    @mock.patch("os.walk")
    def test_get_hash_of_dirs_with_dir_exception(self, walk, path, mock_open):
        mock_open.side_effect = [IOError]
        path.return_value = True
        walk.return_value = [
            ('/foo', ('bar',), ('baz',)),
            ('/foo/bar', (), ('spam', 'eggs')),
        ]
        expected = -2
        actual = misc.get_hash_of_dirs("")

        self.assertEqual(expected, actual)

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

    def test_convert_single_space_to_underscore(self):
        expected = "hello_world"
        actual = misc.convert_to_underscores("hello world")

        self.assertEqual(expected, actual)

    def test_convert_multiple_spaces_to_underscore(self):
        expected = "replacing_spaces_with_underscores_in_a_sentence"
        actual = misc.convert_to_underscores(
            "replacing spaces with underscores in a sentence")

        self.assertEqual(expected, actual)

    def test_convert_multiple_slashes_to_underscore(self):
        expected = "absolute_path_to_file"
        actual = misc.convert_to_underscores("absolute/path/to/file")

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

    @mock.patch("os.listdir")
    def test_find_files_in_folder(self, mock_list_dir):
        mock_list_dir.return_value = [
            "projects.json", "groups.json", "teamcity-0.json", "teamcity-1.json"]

        expected = ["teamcity-0.json", "teamcity-1.json"]
        actual = misc.find_files_in_folder("teamcity")

        self.assertListEqual(expected, actual)

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

    def test_clean_split(self):
        test_string = "/path/to/file"
        expected = ["path", "to", "file"]
        actual = misc.clean_split(test_string, "/")

        self.assertListEqual(expected, actual)

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
