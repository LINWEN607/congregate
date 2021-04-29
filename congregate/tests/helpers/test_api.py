import unittest
from unittest import mock
from pytest import mark
from congregate.helpers.api import GitLabApi
from congregate.helpers.misc_utils import generate_audit_log_message

@mark.unit_test
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.api = GitLabApi()
    
    def test_generate_v4_get_request_url(self):
        url = self.api.generate_v4_request_url("HOST", "API")
        self.assertEqual(url, "%s/api/v4/%s" % ("HOST", "API"))


    def test_generate_v4_get_request_header(self):
        header = self.api.generate_v4_request_header("TOKEN")
        self.assertEqual(header["Private-Token"], "TOKEN")
        self.assertEqual(header["Content-Type"], "application/json")


    @mock.patch("requests.Response")
    @mock.patch("requests.get")
    def test_generate_get_request(self, g, r):
        g.return_value = r
        resp = self.api.generate_get_request("HOST", "TOKEN", "API")
        self.assertIs(resp, r)


    @mock.patch.object(GitLabApi, "generate_v4_request_url")
    @mock.patch("requests.Response")
    @mock.patch("requests.get")
    def test_generate_get_request_calls_generate_v4_request_url_when_url_is_none(self, g, r, u):
        u.return_value = "some_url"
        g.return_value = r
        self.api.generate_get_request("HOST", "TOKEN", "API")
        u.assert_called_once()
        

    @mock.patch.object(GitLabApi, "generate_v4_request_url")
    @mock.patch("requests.Response")
    @mock.patch("requests.get")
    def test_generate_get_request_does_not_call_generate_v4_request_url_when_url_is_not_none(self, g, r, u):
        u.return_value = "some_url"
        g.return_value = r
        self.api.generate_get_request("HOST", "TOKEN", "API", "URL")
        u.assert_not_called()


    @mock.patch.object(GitLabApi, "generate_v4_request_header")
    @mock.patch("requests.Response")
    @mock.patch("requests.get")
    def test_generate_get_request_calls_generate_v4_request_header(self, g, r, h):
        h.return_value = "some_header"
        g.return_value = r
        self.api.generate_get_request("HOST", "TOKEN", "API")
        h.assert_called_once()


    @mock.patch.object(GitLabApi, "generate_v4_request_url")
    @mock.patch("requests.Response")
    @mock.patch("requests.post")
    def test_generate_post_request_calls_generate_v4_request_url(self, p, r, u):
        u.return_value = "some_url"
        p.return_value = r
        self.api.generate_post_request("host", "token", "api", "data")
        u.assert_called_once()


    @mock.patch.object(GitLabApi, "generate_v4_request_header")
    @mock.patch("requests.Response")
    @mock.patch("requests.post")
    def test_generate_post_request_calls_generate_v4_request_header_when_header_is_none(self, p, r, h):
        h.return_value = "some_header"
        p.return_value = r
        self.api.generate_post_request("host", "token", "api", "data")
        h.assert_called_once()


    @mock.patch.object(GitLabApi, "generate_v4_request_header")
    @mock.patch("requests.Response")
    @mock.patch("requests.post")
    def test_generate_post_request_does_not_call_generate_v4_request_header_when_header_is_not_none(self, p, r, h):
        h.return_value = "some_header"
        p.return_value = r
        self.api.generate_post_request("host", "token", "api",
                                "data", headers="some_header")
        h.assert_not_called()


    @mock.patch.object(GitLabApi, "generate_v4_request_url")
    @mock.patch("requests.Response")
    @mock.patch("requests.put")
    def test_generate_put_request_calls_generate_v4_request_url(self, p, r, u):
        u.return_value = "some_url"
        p.return_value = r
        self.api.generate_put_request("host", "token", "api", "data")
        u.assert_called_once()


    @mock.patch.object(GitLabApi, "generate_v4_request_header")
    @mock.patch("requests.Response")
    @mock.patch("requests.put")
    def test_generate_put_request_calls_generate_v4_request_header_when_header_is_none(self, p, r, h):
        h.return_value = "some_header"
        p.return_value = r
        self.api.generate_put_request("host", "token", "api", "data")
        h.assert_called_once()


    @mock.patch.object(GitLabApi, "generate_v4_request_header")
    @mock.patch("requests.Response")
    @mock.patch("requests.put")
    def test_generate_put_request_does_not_call_generate_v4_request_header_when_header_is_not_none(self, p, r, h):
        h.return_value = "some_header"
        p.return_value = r
        self.api.generate_put_request("host", "token", "api",
                                "data", headers="some_header")
        h.assert_not_called()


    @mock.patch.object(GitLabApi, "generate_v4_request_url")
    @mock.patch("requests.Response")
    @mock.patch("requests.delete")
    def test_generate_delete_request_calls_generate_v4_request_url(self, d, r, u):
        u.return_value = "some_url"
        d.return_value = r
        self.api.generate_delete_request("host", "token", "api")
        u.assert_called_once()


    @mock.patch.object(GitLabApi, "generate_v4_request_header")
    @mock.patch("requests.Response")
    @mock.patch("requests.delete")
    def test_generate_delete_request_calls_generate_v4_request_header(self, d, r, h):
        h.return_value = "some_header"
        d.return_value = r
        self.api.generate_delete_request("host", "token", "api")
        h.assert_called_once()


    @mock.patch("requests.head")
    def test_get_total_pages(self, head):
        import requests
        resp = requests.Response()
        resp.headers["X-Total-Pages"] = 10
        head.return_value = resp
        return_resp = self.api.get_total_pages("HOST", "TOKEN", "API")
        self.assertEqual(return_resp, 10)


    @mock.patch("requests.head")
    def test_get_total_pages_on_return_none(self, head):
        import requests
        resp = requests.Response()
        head.return_value = resp
        return_resp = self.api.get_total_pages("HOST", "TOKEN", "API")
        self.assertIsNone(return_resp)


    @mock.patch("requests.head")
    def test_get_count(self, head):
        import requests
        resp = requests.Response()
        resp.headers["X-Total"] = 10
        head.return_value = resp
        return_resp = self.api.get_count("HOST", "TOKEN", "API")
        assert return_resp == 10
        self.assertEqual(return_resp, 10)


    @mock.patch("requests.head")
    def test_get_count_on_return_none(self, head):
        import requests
        resp = requests.Response()
        head.return_value = resp
        return_resp = self.api.get_count("HOST", "TOKEN", "API")
        self.assertIsNone(return_resp)


    @mock.patch("requests.Response")
    @mock.patch("requests.get")
    def test_search(self, g, resp):
        resp.json().return_value = {"abc": 1}
        g.return_value = resp
        j = self.api.search("host", "token", "path", "search_query")
        g.assert_called()
        self.assertEqual(j, resp.json())


    def test_audit_message_with_message(self):
        message = "Modifying some data"
        url = "https://gitlab.test.io"
        req_type = "POST"
        data = {
            "test": "data"
        }

        expected = "Modifying some data by generating POST request to https://gitlab.test.io with data: {'test': 'data'}"
        actual = generate_audit_log_message(req_type, message, url, data)
        self.assertEqual(expected, actual)


    def test_audit_message_without_message(self):
        message = None
        url = "https://gitlab.test.io"
        req_type = "POST"
        data = {
            "test": "data"
        }

        expected = "Generating POST request to https://gitlab.test.io with data: {'test': 'data'}"
        actual = generate_audit_log_message(req_type, message, url, data)
        self.assertEqual(expected, actual)


    def test_audit_message_without_data(self):
        message = "Modifying some data"
        url = "https://gitlab.test.io"
        req_type = "DELETE"
        data = None

        expected = "Modifying some data by generating DELETE request to https://gitlab.test.io"
        actual = generate_audit_log_message(req_type, message, url, data)
        self.assertEqual(expected, actual)


    def test_get_params_none(self):
        params = {
            "page": 5,
            "per_page": 100
        }
        self.assertEqual(params, self.api.get_params(None, 100, 5, False, ""))


    def test_get_params_none_keyset(self):
        params = {
            "pagination": "keyset",
            "per_page": 100,
            "order_by": "id",
            "sort": "asc",
            "id_after": 42
        }
        self.assertEqual(params, self.api.get_params(None, 100, 5, True, 42))


    def test_get_params(self):
        params = {"test": "test"}
        params["page"] = 5
        params["per_page"] = 100
        self.assertEqual(params, self.api.get_params({"test": "test"}, 100, 5, False, ""))


    def test_get_last_id(self):
        links = '<https://gitlab.com/api/v4/projects?id_after=26924&membership=false&order_by=id&owned=false&page=1&pagination=keyset&per_page=100&repository_checksum_failed=false&simple=false&sort=asc&starred=false&statistics=false&wiki_checksum_failed=false&with_custom_attributes=false&with_issues_enabled=false&with_merge_requests_enabled=false>; rel="next"'
        self.assertEqual(self.api.get_last_id(links), "26924")


    def test_get_last_id_none(self):
        self.assertIsNone(self.api.get_last_id(None))
