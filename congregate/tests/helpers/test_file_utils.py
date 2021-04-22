import unittest
from unittest import mock
from pytest import mark
import congregate.helpers.file_utils as futils


@mark.unit_test
class FileUtilsTests(unittest.TestCase):

    @mock.patch("congregate.helpers.file_utils.__get_filename_from_cd")
    @mock.patch("congregate.helpers.file_utils.__is_downloadable")
    @mock.patch("io.TextIOBase")
    @mock.patch("builtins.open")
    @mock.patch("requests.Response")
    @mock.patch("congregate.helpers.file_utils.get")
    def test_download_file_sets_filename_from_response_headers_when_filename_none(
            self, g, resp, o, f, idl, fn):
        fn.return_value = "returned"
        idl.return_value = True
        resp.headers = {"Content-Disposition": "not_returned=returned"}
        o.return_value = f
        g.return_value = resp
        filename = futils.download_file("url", "path")
        self.assertEqual(filename, "returned")

    @mock.patch("congregate.helpers.file_utils.__is_downloadable")
    @mock.patch("io.TextIOBase")
    @mock.patch("builtins.open")
    @mock.patch("requests.Response")
    @mock.patch("congregate.helpers.file_utils.get")
    def test_download_file_uses_filename_from_param(self, g, resp, o, f, idl):
        idl.return_value = True
        resp.headers = {"Content-Disposition": "not_returned=returned"}
        o.return_value = f
        g.return_value = resp
        filename = futils.download_file("url", "path", filename="passed")
        self.assertEqual(filename, "passed")

    @mock.patch("os.path.exists")
    def test_is_recent_file_no_file(self, exists):
        exists.return_value = False
        self.assertFalse(futils.is_recent_file("test"))

    @mock.patch("os.path.exists")
    @mock.patch("os.path.getsize")
    def test_is_recent_file_empty_file(self, size, exists):
        exists.return_value = True
        size.return_value = 0
        self.assertFalse(futils.is_recent_file("test"))

    @mock.patch("os.path.exists")
    @mock.patch("os.path.getsize")
    @mock.patch("os.path.getmtime")
    def test_is_recent_file_not_recent(self, mtime, size, exists):
        exists.return_value = True
        size.return_value = 1
        mtime.return_value = 0
        self.assertFalse(futils.is_recent_file("test"))

    @mock.patch("os.path.exists")
    @mock.patch("os.path.getsize")
    @mock.patch("os.path.getmtime")
    def test_is_recent_file(self, mtime, size, exists):
        exists.return_value = True
        size.return_value = 1
        mtime.return_value = 9999999999
        self.assertTrue(futils.is_recent_file("test"))

    @mock.patch("os.path.exists")
    def test_get_hash_of_dirs_no_dir(self, path):
        path.return_value = False
        expected = -1
        actual = futils.get_hash_of_dirs("")

        self.assertEqual(expected, actual)

    @mock.patch("os.path.exists")
    @mock.patch("os.walk")
    def test_get_hash_of_dirs_with_exception(self, walk, path):
        path.return_value = True
        walk.side_effect = [Exception]
        expected = -2
        actual = futils.get_hash_of_dirs("")

        self.assertEqual(expected, actual)

    @mock.patch("congregate.helpers.file_utils.open",
                new=mock.mock_open(read_data=b"def456"))
    @mock.patch("os.path.exists")
    @mock.patch("os.walk")
    def test_get_hash_of_dirs_with_dir(self, walk, path):
        path.return_value = True
        walk.return_value = [
            ('/foo', ('bar',), ('baz',)),
            ('/foo/bar', (), ('spam', 'eggs')),
        ]
        expected = "b981b8d32b55cbddc5c192bed125dc5fe42eb922"
        actual = futils.get_hash_of_dirs("")

        self.assertEqual(expected, actual)

    @mock.patch("os.listdir")
    def test_find_files_in_folder(self, mock_list_dir):
        mock_list_dir.return_value = [
            "projects.json", "groups.json", "teamcity-0.json", "teamcity-1.json"]

        expected = ["teamcity-0.json", "teamcity-1.json"]
        actual = futils.find_files_in_folder("teamcity", "data")

        self.assertListEqual(expected, actual)

    @mock.patch("congregate.helpers.file_utils.open")
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
        actual = futils.get_hash_of_dirs("")

        self.assertEqual(expected, actual)

    @mock.patch("os.path.exists")
    @mock.patch("os.makedirs")
    def test_create_local_project_export_structure(
            self, mock_make_dirs, mock_exists):
        mock_exists.return_value = False
        futils.create_local_project_export_structure("/a/b/c")
        mock_make_dirs.assert_called_with("/a/b/c")
