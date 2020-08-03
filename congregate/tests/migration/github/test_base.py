import responses
from mock import patch, PropertyMock
from congregate.tests.mockapi.github.headers import MockHeaders
from congregate.migration.github.api.base import GitHubApi as GitHubApi


def test_generate_v3_request_header():
    r = {"Accept": "application/vnd.github.v3+json", "Authorization": 'token TOKEN'}
    ut = GitHubApi("HOST", "TOKEN")
    resp = ut.generate_v3_request_header("TOKEN")
    assert resp == r


def test_generate_v4_request_header():
    r = {"Authorization": 'Bearer TOKEN'}
    ut = GitHubApi("HOST", "TOKEN")
    resp = ut.generate_v4_request_header("TOKEN")
    assert resp == r


def test_generate_v3_request_url():
    r = "HOST/api/v3/ORGANIZATION"
    ut = GitHubApi("HOST", "TOKEN")
    resp = ut.generate_v3_request_url("HOST", "ORGANIZATION")
    assert resp == r
    resp = ut.generate_v3_request_url("HOST/", "ORGANIZATION")
    assert resp == r

def test_generate_v3_get_request():
    with patch("congregate.migration.github.api.base.requests.Response") as mock_resp:
        with patch("congregate.migration.github.api.base.requests.get") as mock_get:
            t = GitHubApi("HOST", "TOKEN")
            mock_get.return_value = mock_resp
            resp = t.generate_v3_get_request("HOST", "TOKEN", "API")
            assert mock_resp is resp

def test_generate_v4_request_url():
    r = "HOST/api/graphql"
    ut = GitHubApi("HOST", "TOKEN")
    resp = ut.generate_v4_request_url("HOST")
    assert resp == r
    resp = ut.generate_v4_request_url("HOST/")
    assert resp == r


def test_replace_unwanted_characters():
    r = "abcdef"
    ut = GitHubApi("HOST", "TOKEN")
    resp = ut.replace_unwanted_characters('abc <>"def')
    assert resp == r


def test_create_v4_query():
    r = None
    ut = GitHubApi("HOST", "TOKEN")
    resp = ut.create_v4_query("QUERY")
    assert resp == r


def test_create_dict_from_headers():
    r = "https://github.gitlab-proserv.net/api/v3/organizations?since=12"
    test_headers = MockHeaders().get_linked_headers()
    ut = GitHubApi("HOST", "TOKEN")
    resp = ut.create_dict_from_headers(test_headers.get("Link"))
    assert resp['next'] == r

# pylint: disable=no-member
@responses.activate
def test_list_all_single_page():
    r = MockHeaders()
    responses.add(
        responses.GET,
        "http://host/api/v3/organizations?per_page=1000",
        headers=r.get_linkless_headers(),
        status=200,
        json=r.get_data(),
        content_type='text/json',
        match_querystring=False)

    ut = GitHubApi("http://host", "TOKEN")
    actual = ut.list_all("http://host", "organizations", verify=False)
    expected = r.get_data()
    assert expected == actual

@responses.activate
def test_list_all_multipage():
    pass

# pylint: disable=no-member
@responses.activate
def test_list_all_bad_status_code():
    r = MockHeaders()
    responses.add(
        responses.GET,
        "http://host/api/v3/organizations?per_page=1000",
        headers=r.get_linkless_headers(),
        status=500,
        json=r.get_data(),
        content_type='text/json',
        match_querystring=False)

    ut = GitHubApi("http://host", "TOKEN")
    actual = ut.list_all("http://host", "organizations", verify=False)
    expected = None
    assert expected == actual
