import unittest
import responses
from unittest.mock import patch
from pytest import mark
from congregate.tests.mockapi.github.headers import MockHeaders
from congregate.migration.github.api.base import GitHubApi


@mark.unit_test
class BaseTests(unittest.TestCase):

    def setUp(self):
        self.mock_headers = MockHeaders()
        self.api = GitHubApi("http://github.com", "TOKEN")

    def test_generate_v3_request_header(self):
        r = {"Accept": "application/vnd.github.v3+json",
             "Authorization": 'token TOKEN'}
        resp = self.api.generate_v3_request_header("TOKEN")
        self.assertEqual(resp, r)

    def test_generate_v3_basic_auth_request_header(self):
        r = {"Accept": "application/vnd.github.v3+json"}
        resp = self.api.generate_v3_basic_auth_request_header()
        self.assertEqual(resp, r)

    def test_generate_v3_basic_auth(self):
        r = ("user", "pass")
        resp = self.api.generate_v3_basic_auth("user", "pass")
        self.assertEqual(resp, r)

    def test_generate_v4_request_header(self):
        r = {"Authorization": 'Bearer TOKEN'}
        resp = self.api.generate_v4_request_header("TOKEN")
        self.assertEqual(resp, r)

    def test_generate_v3_request_url(self):
        r = "HOST/api/v3/ORGANIZATION"
        resp = self.api.generate_v3_request_url("HOST", "ORGANIZATION")
        self.assertEqual(resp, r)
        resp = self.api.generate_v3_request_url("HOST/", "ORGANIZATION")
        self.assertEqual(resp, r)
        resp = self.api.generate_v3_request_url(
            "https://api.github.com", "users")
        self.assertEqual(resp, "https://api.github.com/users")

    def test_generate_v3_get_request(self):
        with patch("congregate.migration.github.api.base.requests.Response") as mock_resp:
            with patch("congregate.migration.github.api.base.requests.get") as mock_get:
                mock_get.return_value = mock_resp
                resp = self.api.generate_v3_get_request("HOST", "API")
                self.assertEqual(mock_resp, resp)

    def test_generate_v3_basic_auth_get_request(self):
        with patch("congregate.migration.github.api.base.requests.Response") as mock_resp:
            with patch("congregate.migration.github.api.base.requests.get") as mock_get:
                mock_get.return_value = mock_resp
                resp = self.api.generate_v3_get_request(
                    "HOST", "API", "USERNAME", "PASSWORD")
                self.assertEqual(mock_resp, resp)

    def test_generate_v4_request_url(self):
        r = "HOST/api/graphql"
        resp = self.api.generate_v4_request_url("HOST")
        self.assertEqual(resp, r)
        resp = self.api.generate_v4_request_url("HOST/")
        self.assertEqual(resp, r)
        resp = self.api.generate_v4_request_url("https://api.github.com")
        self.assertEqual(resp, "https://api.github.com/graphql")

    def test_replace_unwanted_characters(self):
        r = "abcdef"
        resp = self.api.replace_unwanted_characters('abc <>"def')
        self.assertEqual(resp, r)

    def test_create_dict_from_headers(self):
        r = "https://github.example.net/api/v3/organizations?since=12"
        test_headers = self.mock_headers.get_linked_headers()
        resp = self.api.create_dict_from_headers(test_headers.get("Link"))
        self.assertEqual(resp["next"], r)

    # pylint: disable=no-member

    @responses.activate
    def test_list_all_single_page(self):
        responses.add(
            responses.GET,
            "http://host/api/v3/organizations?per_page=1000",
            headers=self.mock_headers.get_linkless_headers(),
            status=200,
            json=self.mock_headers.get_data(),
            content_type='text/json',
            match_querystring=False)

        actual = list(self.api.list_all(
            "http://host", "organizations"))
        expected = self.mock_headers.get_data()
        self.assertEqual(expected, actual)

    @responses.activate
    def test_list_all_multipage(self):
        responses.add(
            responses.GET,
            "https://github.example.net/api/v3/organizations",
            headers=self.mock_headers.get_linked_headers(),
            status=200,
            json=self.mock_headers.get_data()[0],
            content_type='text/json',
            match_querystring=False)

        responses.add(
            responses.GET,
            "https://github.example.net/api/v3/organizations?since=12",
            headers=self.mock_headers.get_page_2_linked_headers(),
            status=200,
            json=self.mock_headers.get_data()[1],
            content_type='text/json',
            match_querystring=False)

        responses.add(
            responses.GET,
            "https://github.example.net/api/v3/organizations?since=24",
            headers=self.mock_headers.get_linkless_headers(),
            status=200,
            json=self.mock_headers.get_data()[2],
            content_type='text/json',
            match_querystring=False)

        actual = list(self.api.list_all(
            "https://github.example.net", "organizations", limit=1))
        expected = self.mock_headers.get_data()
        self.assertEqual(expected, actual)

    # pylint: disable=no-member

    @responses.activate
    def test_list_all_bad_status_code(self):
        responses.add(
            responses.GET,
            "http://host/api/v3/organizations?per_page=1000",
            headers=self.mock_headers.get_linkless_headers(),
            status=500,
            json=self.mock_headers.get_data(),
            content_type='text/json',
            match_querystring=False)

        actual = list(self.api.list_all(
            "http://host", "organizations"))
        expected = []
        self.assertEqual(expected, actual)

    # pylint: disable=no-member

    # @responses.activate
    # def test_list_all_raise_error(self):
    #     responses.add(
    #         responses.GET,
    #         "http://host/api/v3/organizations?per_page=1000",
    #         headers=self.mock_headers.get_linkless_headers(),
    #         status=422,
    #         json=self.mock_headers.get_data(),
    #         content_type='text/json',
    #         match_querystring=False)

    #     with self.assertRaises(ValueError):
    #         self.api.list_all("http://host", "organizations", verify=False)

    def test_generate_v3_post_request(self):
        with patch("congregate.migration.github.api.base.requests.Response") as mock_resp:
            with patch("congregate.migration.github.api.base.requests.post") as mock_post:
                mock_post.return_value = mock_resp
                resp = self.api.generate_v3_post_request(
                    "HOST", "API", {"data": "data"})
                self.assertEqual(mock_resp, resp)
