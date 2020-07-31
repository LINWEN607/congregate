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

# # pylint: disable=no-member
# @responses.activate
# @mock.patch("congregate.helpers.api.generate_get_request")
# def test_list_all():
#     r = None
#     ut = GitHubApi("HOST", "TOKEN")



    # # pylint: disable=no-member
    # @responses.activate
    # @mock.patch("congregate.helpers.api.list_all")
    # @mock.patch("congregate.helpers.api.generate_get_request")
    # def test_is_group_non_empty_true_subgroups(self, mock_get_api, mock_list_all):
    #     url_value = "https://gitlab.com/api/v4/groups"
    #     mock_list_all.return_value = self.mock_groups.get_all_subgroups_list()
    #     responses.add(
    #         responses.GET,
    #         url_value,
    #         json=self.mock_groups.get_group(),
    #         status=200,
    #         content_type='text/json',
    #         match_querystring=True)
    #     group = self.mock_groups.get_group()
    #     group["projects"] = []
    #     self.assertTrue(self.groups.is_group_non_empty(group))




def test_generate_v3_get_request():
    with mock.patch("congregate.migration.github.api.base.requests.Response") as mock_resp:
        with mock.patch("congregate.migration.github.api.base.requests.get") as mock_get:
            t = GitHubApi("HOST", "TOKEN")
            mock_get.return_value = mock_resp
            resp = t.generate_v3_get_request("HOST", "TOKEN", "API")
            assert mock_resp is resp
