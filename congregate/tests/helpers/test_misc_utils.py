from datetime import datetime, timedelta
import mock
from congregate.tests.helpers.mock_data.results import MockProjectResults
import congregate.helpers.misc_utils as misc


def test_remove_dupes_no_dupes():
    L = [{'id': 1, 'name': 'john', 'age': 34}, {'id': 2, 'name': 'jack',
                                                'age': 34}, {'id': 3, 'name': 'hanna', 'age': 30}]
    de_duped = misc.remove_dupes(L)
    assert de_duped == L


def test_remove_dupes_with_dupes():
    L = [{'id': 1, 'name': 'john', 'age': 34}, {'id': 1, 'name': 'john', 'age': 34}, {'id': 2, 'name': 'jack', 'age': 34}, {
        'id': 2, 'name': 'jack', 'age': 34}, {'id': 3, 'name': 'hanna', 'age': 30}, {'id': 3, 'name': 'hanna', 'age': 30}]
    de_duped = misc.remove_dupes(L)
    assert de_duped == [{'id': 1, 'name': 'john', 'age': 34}, {
        'id': 2, 'name': 'jack', 'age': 34}, {'id': 3, 'name': 'hanna', 'age': 30}]


def test_remove_dupes_with_empty_returns_empty():
    de_duped = misc.remove_dupes([])
    assert de_duped == []


def test_remove_dupes_with_all_dupes_returns_single():
    L = [{'id': 1, 'name': 'john', 'age': 34}, {
        'id': 1, 'name': 'john', 'age': 34}, {'id': 1, 'name': 'john', 'age': 34}]
    de_duped = misc.remove_dupes(L)
    assert de_duped == [{'id': 1, 'name': 'john', 'age': 34}]


@mock.patch("congregate.helpers.misc_utils.__get_filename_from_cd")
@mock.patch("congregate.helpers.misc_utils.__is_downloadable")
@mock.patch("io.TextIOBase")
@mock.patch("builtins.open")
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
@mock.patch("io.TextIOBase")
@mock.patch("builtins.open")
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


def test_get_dry_log():
    assert misc.get_dry_log() == "DRY-RUN: "
    assert misc.get_dry_log(False) == ""
    assert misc.get_dry_log("whatever") == "DRY-RUN: "


def test_get_rollback_log():
    assert misc.get_rollback_log() == ""
    assert misc.get_rollback_log(True) == "Rollback: "
    assert misc.get_rollback_log("whatever") == "Rollback: "


@mock.patch("getpass.getpass")
def test_obfuscate(secret):
    secret.return_value = "test"
    assert misc.obfuscate("Enter secret: ") == "dGVzdA=="


def test_deobfuscate():
    assert misc.deobfuscate("dGVzdA==") == "test"


@mock.patch("os.path.exists")
def test_is_recent_file_no_file(exists):
    exists.return_value = False
    assert misc.is_recent_file("test") is False


@mock.patch("os.path.exists")
@mock.patch("os.path.getsize")
def test_is_recent_file_empty_file(size, exists):
    exists.return_value = True
    size.return_value = 0
    assert misc.is_recent_file("test") is False


@mock.patch("os.path.exists")
@mock.patch("os.path.getsize")
@mock.patch("os.path.getmtime")
def test_is_recent_file_not_recent(mtime, size, exists):
    exists.return_value = True
    size.return_value = 1
    mtime.return_value = 0
    assert misc.is_recent_file("test") is False


@mock.patch("os.path.exists")
@mock.patch("os.path.getsize")
@mock.patch("os.path.getmtime")
def test_is_recent_file(mtime, size, exists):
    exists.return_value = True
    size.return_value = 1
    mtime.return_value = 9999999999
    assert misc.is_recent_file("test") is True


def test_rewrite_json_list_into_dict():
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

    assert misc.rewrite_json_list_into_dict(initial) == expected


def test_is_dot_com():
    assert misc.is_dot_com("asdasd") is False
    assert misc.is_dot_com("https://gitlab.com") is True


def test_check_is_project_or_group_for_logging_project():
    assert misc.check_is_project_or_group_for_logging(True) is "Project"
    assert misc.check_is_project_or_group_for_logging(False) is "Group"


def test_get_timedelta_older_than_twenty_four_hours():
    timestamp = "2020-03-10T17:09:32.322Z"
    assert misc.get_timedelta(timestamp) > 24


def test_get_timedelta_older_than_twenty_four_hours_different_format():
    timestamp = "2013-09-30T13:46:02Z"
    assert misc.get_timedelta(timestamp) > 24


def test_get_timedelta_newer_than_twenty_four_hours():
    timestamp = str(datetime.now()).replace(" ", "T")
    assert misc.get_timedelta(timestamp) < 24


def test_get_timedelta_exactly_twenty_four_hours():
    timestamp = str(datetime.today() - timedelta(days=1)).replace(" ", "T")
    assert misc.get_timedelta(timestamp) == 24


def test_validate_name():
    assert misc.validate_name(
        ":: This.is-how/WE do\n&it") == "This is how WE do it"


@mock.patch("congregate.helpers.misc_utils.read_json_file_into_object")
@mock.patch("glob.glob")
def test_stitch_json(glob, json):
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

    assert expected == actual


@mock.patch("congregate.helpers.misc_utils.read_json_file_into_object")
@mock.patch("glob.glob")
def test_stitch_json_too_many_steps(glob, json):
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

    assert expected == actual


@mock.patch("requests.Response")
def test_safe_json_response_with_exception(response):
    response.json.side_effect = [ValueError]
    expected = None
    actual = misc.safe_json_response(response)

    assert expected == actual


@mock.patch("requests.Response")
def test_safe_json_response_without_exception(response):
    response.json.side_effect = [{"hello": "world"}]
    expected = {"hello": "world"}
    actual = misc.safe_json_response(response)

    assert expected == actual


@mock.patch("congregate.helpers.misc_utils.open", new=mock.mock_open(read_data=b"abc123"))
@mock.patch("congregate.helpers.misc_utils.get_hash_of_dirs")
def test_is_ui_out_of_date_false(mock_hash):
    mock_hash.return_value = b"abc123"
    expected = False
    actual = misc.is_ui_out_of_date("")

    assert expected == actual


@mock.patch("congregate.helpers.misc_utils.open", new=mock.mock_open(read_data=b"def456"))
@mock.patch("congregate.helpers.misc_utils.get_hash_of_dirs")
def test_is_ui_out_of_date_true(mock_hash):
    mock_hash.return_value = b"abc123"
    expected = True
    actual = misc.is_ui_out_of_date("")

    assert expected == actual


@mock.patch("congregate.helpers.misc_utils.open")
@mock.patch("congregate.helpers.misc_utils.get_hash_of_dirs")
def test_is_ui_out_of_date_true_with_exception(mock_hash, mock_open):
    mock_open.side_effect = [IOError]
    mock_hash.return_value = b"abc123"
    expected = True
    actual = misc.is_ui_out_of_date("")

    assert expected == actual


@mock.patch("os.path.exists")
def test_get_hash_of_dirs_no_dir(path):
    path.return_value = False
    expected = -1
    actual = misc.get_hash_of_dirs("")

    assert expected == actual


@mock.patch("os.path.exists")
@mock.patch("os.walk")
def test_get_hash_of_dirs_with_exception(walk, path):
    path.return_value = True
    walk.side_effect = [Exception]
    expected = -2
    actual = misc.get_hash_of_dirs("")

    assert expected == actual


@mock.patch("congregate.helpers.misc_utils.open", new=mock.mock_open(read_data=b"def456"))
@mock.patch("os.path.exists")
@mock.patch("os.walk")
def test_get_hash_of_dirs_with_dir(walk, path):
    path.return_value = True
    walk.return_value = [
        ('/foo', ('bar',), ('baz',)),
        ('/foo/bar', (), ('spam', 'eggs')),
    ]
    expected = "b981b8d32b55cbddc5c192bed125dc5fe42eb922"
    actual = misc.get_hash_of_dirs("")

    assert expected == actual


@mock.patch("congregate.helpers.misc_utils.open")
@mock.patch("os.path.exists")
@mock.patch("os.walk")
def test_get_hash_of_dirs_with_dir_exception(walk, path, mock_open):
    mock_open.side_effect = [IOError]
    path.return_value = True
    walk.return_value = [
        ('/foo', ('bar',), ('baz',)),
        ('/foo/bar', (), ('spam', 'eggs')),
    ]
    expected = -2
    actual = misc.get_hash_of_dirs("")

    assert expected == actual
