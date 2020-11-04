import unittest
import pytest
import responses
from congregate.migration.github.meta.github_browser import GitHubBrowser

@pytest.mark.unit_test
class GitHubBrowserTests(unittest.TestCase):
    @responses.activate
    def test_scrape_email(self):
        html_snippet = """
        <div class="site-admin-box">
            <h4>
                <svg class="octicon octicon-info" viewBox="0 0 14 16" version="1.1" width="14" height="16" aria-hidden="true"><path fill-rule="evenodd" d="M6.3 5.69a.942.942 0 01-.28-.7c0-.28.09-.52.28-.7.19-.18.42-.28.7-.28.28 0 .52.09.7.28.18.19.28.42.28.7 0 .28-.09.52-.28.7a1 1 0 01-.7.3c-.28 0-.52-.11-.7-.3zM8 7.99c-.02-.25-.11-.48-.31-.69-.2-.19-.42-.3-.69-.31H6c-.27.02-.48.13-.69.31-.2.2-.3.44-.31.69h1v3c.02.27.11.5.31.69.2.2.42.31.69.31h1c.27 0 .48-.11.69-.31.2-.19.3-.42.31-.69H8V7.98v.01zM7 2.3c-3.14 0-5.7 2.54-5.7 5.68 0 3.14 2.56 5.7 5.7 5.7s5.7-2.55 5.7-5.7c0-3.15-2.56-5.69-5.7-5.69v.01zM7 .98c3.86 0 7 3.14 7 7s-3.14 7-7 7-7-3.12-7-7 3.14-7 7-7z"></path></svg>
                <img src="https://github.gitlab-proserv.net/avatars/u/11?s=100" width="50" height="50" alt="@jdoe" class=" avatar-user" />
                <a href="/stafftools/users/jdoe/overview">User info</a>
            </h4>
            <ul class="site-admin-detail-list">
                <li>
                <svg class="octicon octicon-octoface" viewBox="0 0 16 16" version="1.1" width="16" height="16" aria-hidden="true"><path fill-rule="evenodd" d="M14.7 5.34c.13-.32.55-1.59-.13-3.31 0 0-1.05-.33-3.44 1.3-1-.28-2.07-.32-3.13-.32s-2.13.04-3.13.32c-2.39-1.64-3.44-1.3-3.44-1.3-.68 1.72-.26 2.99-.13 3.31C.49 6.21 0 7.33 0 8.69 0 13.84 3.33 15 7.98 15S16 13.84 16 8.69c0-1.36-.49-2.48-1.3-3.35zM8 14.02c-3.3 0-5.98-.15-5.98-3.35 0-.76.38-1.48 1.02-2.07 1.07-.98 2.9-.46 4.96-.46 2.07 0 3.88-.52 4.96.46.65.59 1.02 1.3 1.02 2.07 0 3.19-2.68 3.35-5.98 3.35zM5.49 9.01c-.66 0-1.2.8-1.2 1.78s.54 1.79 1.2 1.79c.66 0 1.2-.8 1.2-1.79s-.54-1.78-1.2-1.78zm5.02 0c-.66 0-1.2.79-1.2 1.78s.54 1.79 1.2 1.79c.66 0 1.2-.8 1.2-1.79s-.53-1.78-1.2-1.78z"></path></svg>
                    S jdoe
                <small>
                    &ndash;
                    <a href="https://github.gitlab-proserv.net/jdoe">View profile</a>
                </small>
                </li>
                <li>
                    <svg class="octicon octicon-mail" viewBox="0 0 14 16" version="1.1" width="14" height="16" aria-hidden="true"><path fill-rule="evenodd" d="M0 4v8c0 .55.45 1 1 1h12c.55 0 1-.45 1-1V4c0-.55-.45-1-1-1H1c-.55 0-1 .45-1 1zm13 0L7 9 1 4h12zM1 5.5l4 3-4 3v-6zM2 12l3.5-3L7 10.5 8.5 9l3.5 3H2zm11-.5l-4-3 4-3v6z"></path></svg>
                    jdoe@gitlab.com
                    <small>
                    <br>
                    <a href="/stafftools/users/jdoe/emails">and 0 more</a>
                    </small>
                </li>

                <li>
                    <svg class="octicon octicon-primitive-dot text-red" viewBox="0 0 8 16" version="1.1" width="8" height="16" aria-hidden="true"><path fill-rule="evenodd" d="M0 8c0-2.2 1.8-4 4-4s4 1.8 4 4-1.8 4-4 4-4-1.8-4-4z"></path></svg>
                    <a href="/stafftools/users/jdoe/activity">Dormant</a>
                </li>
            </ul>
        </div>
        """

        auth_token = """
            <ul class="list-style-none d-flex flex-wrap ">
                <li class="mr-3">&copy; 2020 GitHub, Inc.</li>
                    <li class="mr-3"><a href="https://help.github.com/enterprise/2.21">Help</a></li>
                    <li><a href="/contact">Support</a></li>
                    <li class="ml-3"><!-- '"` --><!-- </textarea></xmp> --></option></form><form class="js-stats-toggle" action="/site/toggle_site_admin_and_employee_status" accept-charset="UTF-8" method="post"><input type="hidden" name="authenticity_token" value="ixpVu7QRzVwO03u+30yEk6fMu4T7WdDWevaLsrdkgR/sGD0Xs1k3axvZ4Ig8G807ciVhCtHtmuqd/BzGsa87YQ==" />
                    <button type="submit" class="btn-link" data-hotkey="`,S">
                        Site admin mode
                        on
                    </button>
                    </form>
                </li>
            </ul>
        """
        # pylint: disable=no-member
        responses.add(responses.GET, "http://github.example.com",
                      body=auth_token, status=200, content_type='text/html', match_querystring=True)
        responses.add(responses.POST, "http://github.example.com/session",
                      body=None, status=200, content_type='text/html', match_querystring=True)
        responses.add(responses.GET, "http://github.example.com/stafftools/users/jdoe",
                      body=html_snippet, status=200, content_type='text/html', match_querystring=True)
        # pylint: enable=no-member
        browser = GitHubBrowser(
            "http://github.example.com", "admin", "password")
        actual = browser.scrape_user_email("jdoe")

        expected = "jdoe@gitlab.com"

        self.assertEqual(actual, expected)
