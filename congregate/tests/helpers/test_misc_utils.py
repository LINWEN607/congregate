import pytest
import mock
import congregate.helpers.misc_utils as misc

def test_remove_dupes_no_dupes():
    de_duped = misc.remove_dupes([1, 2, 3])
    assert de_duped == [1, 2, 3]


def test_remove_dupes_with_dupes():
    de_duped = misc.remove_dupes([1, 1, 2, 2, 3, 3])
    assert de_duped == [1, 2, 3]


def test_remove_dupes_with_empty_returns_empty():
    de_duped = misc.remove_dupes([])
    assert de_duped == []


def test_remove_dupes_with_all_dupes_returns_single():
    de_duped = misc.remove_dupes([1, 1, 1])
    assert de_duped == [1]


@mock.patch("congregate.helpers.misc_utils.__get_filename_from_cd")
@mock.patch("congregate.helpers.misc_utils.__is_downloadable")
@mock.patch("__builtin__.file")
@mock.patch("__builtin__.open")
@mock.patch("requests.Response")
@mock.patch("congregate.helpers.misc_utils.get")
def test_download_file_sets_filename_from_response_headers_when_filename_none(g, resp, o, f, idl, fn):
    fn.return_value = "returned"
    idl.return_value = True
    resp.headers = {"Content-Disposition": "not_returned=returned"}
    o.return_value = f
    g.return_value = resp
    filename = misc.download_file("url", "path")
    assert filename == "returned"


@mock.patch("congregate.helpers.misc_utils.__is_downloadable")
@mock.patch("__builtin__.file")
@mock.patch("__builtin__.open")
@mock.patch("requests.Response")
@mock.patch("congregate.helpers.misc_utils.get")
def test_download_file_uses_filename_from_param(g, resp, o, f, idl):
    idl.return_value = True
    resp.headers = {"Content-Disposition": "not_returned=returned"}
    o.return_value = f
    g.return_value = resp
    filename = misc.download_file("url", "path", filename="passed")
    assert filename == "passed"


@mock.patch("os.path.exists")
@mock.patch("os.makedirs")
def test_create_local_project_export_structure(mock_make_dirs, mock_exists):
    mock_exists.return_value = False
    misc.create_local_project_export_structure("/a/b/c")
    mock_make_dirs.assert_called_with("/a/b/c")


def test_strip_numbers():
    stripped = misc.strip_numbers("aaa98bbb98hhh222133")
    assert stripped == "aaabbbhhh"


def test_strip_numbers_returns_empty():
    stripped = misc.strip_numbers("12345")
    assert stripped == ""


def test_strip_numbers_returns_string_on_no_numbers():
    stripped = misc.strip_numbers("ABCD")
    assert stripped == "ABCD"


def test_parse_query_params():
    qp = misc.parse_query_params({"abc": 1})
    assert qp == "?abc=1"


def test_parse_query_params_on_empty():
    qp = misc.parse_query_params({})
    assert qp == ""


def test_parse_query_params_on_none():
    qp = misc.parse_query_params({"abc": None})
    assert qp == ""


@mock.patch("os.getenv")
@mock.patch("os.getcwd")
def test_get_congregate_path_with_no_env_set(get_cwd, get_env):
    get_env.return_value = None
    get_cwd.return_value = "FAKEPATH"
    app_path = misc.get_congregate_path()
    assert app_path == "FAKEPATH"


@mock.patch("os.getenv")
def test_get_congregate_path_with_env_set(get_env):
    get_env.return_value = "FAKEPATH"
    app_path = misc.get_congregate_path()
    assert app_path == "FAKEPATH"
