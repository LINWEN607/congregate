import mock

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
    r = "https://github.gitlab-proserv.net/api/v3/organizations?since=10"
    link_headers = '<https://github.gitlab-proserv.net/api/v3/organizations?since=10>; rel="next", <https://github.gitlab-proserv.net/api/v3/organizations{?since}>; rel="first"'
    ut = GitHubApi("HOST", "TOKEN")
    resp = ut.create_dict_from_headers(link_headers)
    assert resp['next'] == r


def test_list_all():
    pass
    # TODO:
    #   1. Mock the data
    #   2. Mock the request call
    #   3. Mock the response
    # r = None
    # ut = GitHubApi("HOST", "TOKEN")
    # ut.list_all("HOST", "organizations", verify=False)


def test_generate_v3_get_request():
    with mock.patch("congregate.migration.github.api.base.requests.Response") as mock_resp:
        with mock.patch("congregate.migration.github.api.base.requests.get") as mock_get:
            t = GitHubApi("HOST", "TOKEN")
            mock_get.return_value = mock_resp
            resp = t.generate_v3_get_request("HOST", "TOKEN", "API")
            assert mock_resp is resp
