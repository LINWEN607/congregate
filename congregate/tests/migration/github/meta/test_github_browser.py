import unittest
import pytest
import responses
from congregate.migration.github.meta.github_browser import GitHubBrowser
from congregate.tests.mockapi.github.scrape import GitHubWebPageScrape

@pytest.mark.unit_test
class GitHubBrowserTests(unittest.TestCase):
    @responses.activate
    def test_scrape_email(self):
        scrape = GitHubWebPageScrape()
        # pylint: disable=no-member
        responses.add(responses.GET, "http://github.example.com",
                      body=scrape.auth_token(), status=200, content_type='text/html', match_querystring=True)
        responses.add(responses.POST, "http://github.example.com/session",
                      body=None, status=200, content_type='text/html', match_querystring=True)
        responses.add(responses.GET, "http://github.example.com/stafftools/users/jdoe",
                      body=scrape.html_snippet(), status=200, content_type='text/html', match_querystring=True)
        responses.add(responses.GET, "http://github.example.com/stafftools/users/admin",
                      body=scrape.html_snippet(), status=200, content_type='text/html', match_querystring=True)
        # pylint: enable=no-member
        browser = GitHubBrowser(
            "http://github.example.com", "admin", "password")
        actual = browser.scrape_user_email("jdoe")

        expected = "jdoe@gitlab.com"

        self.assertEqual(actual, expected)
