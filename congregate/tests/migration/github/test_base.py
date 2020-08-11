import unittest
import responses
from mock import patch, PropertyMock, MagicMock
from congregate.tests.mockapi.github.headers import MockHeaders
from congregate.migration.github.api.base import GitHubApi


class BaseTests(unittest.TestCase):

    def setUp(self):
        self.mock_headers = MockHeaders()
        self.api = GitHubApi("http://github.com", "TOKEN")

    def test_generate_v3_request_header(self):
        r = {"Accept": "application/vnd.github.v3+json",
             "Authorization": 'token TOKEN'}
        resp = self.api.generate_v3_request_header("TOKEN")
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

    def test_generate_v3_get_request(self):
        with patch("congregate.migration.github.api.base.requests.Response") as mock_resp:
            with patch("congregate.migration.github.api.base.requests.get") as mock_get:
                mock_get.return_value = mock_resp
                resp = self.api.generate_v3_get_request("HOST", "API")
                self.assertEqual(mock_resp, resp)

    def test_generate_v4_request_url(self):
        r = "HOST/api/graphql"
        resp = self.api.generate_v4_request_url("HOST")
        self.assertEqual(resp, r)
        resp = self.api.generate_v4_request_url("HOST/")
        self.assertEqual(resp, r)

    def test_replace_unwanted_characters(self):
        r = "abcdef"
        resp = self.api.replace_unwanted_characters('abc <>"def')
        self.assertEqual(resp, r)

    def test_create_dict_from_headers(self):
        r = "https://github.gitlab-proserv.net/api/v3/organizations?since=12"
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

        actual = self.api.list_all(
            "http://host", "organizations", verify=False)
        expected = self.mock_headers.get_data()
        self.assertEqual(expected, actual)

    @patch.object(GitHubApi, "generate_v3_get_request")
    def test_list_all_multipage(self, mock_get):
        mock_page1 = MagicMock()
        type(mock_page1).status_code = PropertyMock(return_value=200)
        mock_page1.headers = self.mock_headers.get_linked_headers()
        mock_page1.json.return_value = [self.mock_headers.get_data()[0]]
        mock_page2 = MagicMock()
        type(mock_page2).status_code = PropertyMock(return_value=200)
        mock_page2.headers = self.mock_headers.get_linked_headers()
        mock_page2.json.return_value = [self.mock_headers.get_data()[1]]
        mock_page3 = MagicMock()
        type(mock_page3).status_code = PropertyMock(return_value=200)
        mock_page3.headers = self.mock_headers.get_linkless_headers()
        mock_page3.json.return_value = [self.mock_headers.get_data()[2]]
        mock_get.side_effect = [mock_page1, mock_page2, mock_page3]

        actual = self.api.list_all(
            "http://host", "organizations", verify=False)
        expected = self.mock_headers.get_data()
        self.assertEqual(expected, actual)

    # pylint: disable=no-member

    @ responses.activate
    def test_list_all_bad_status_code(self):
        responses.add(
            responses.GET,
            "http://host/api/v3/organizations?per_page=1000",
            headers=self.mock_headers.get_linkless_headers(),
            status=500,
            json=self.mock_headers.get_data(),
            content_type='text/json',
            match_querystring=False)

        actual = self.api.list_all(
            "http://host", "organizations", verify=False)
        expected = None
        self.assertEqual(expected, actual)

    # pylint: disable=no-member

    @ responses.activate
    def test_list_all_raise_error(self):
        responses.add(
            responses.GET,
            "http://host/api/v3/organizations?per_page=1000",
            headers=self.mock_headers.get_linkless_headers(),
            status=422,
            json=self.mock_headers.get_data(),
            content_type='text/json',
            match_querystring=False)

        with self.assertRaises(ValueError):
            self.api.list_all("http://host", "organizations", verify=False)
