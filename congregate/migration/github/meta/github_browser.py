import mechanize
from bs4 import BeautifulSoup as bs
from congregate.helpers.logger import myLogger

class GitHubBrowser(mechanize.Browser):
    def __init__(self, host, username, password):
        super(GitHubBrowser, self).__init__()
        self.log = myLogger(__name__)
        self.host = host
        # pylint: disable=no-member
        self.set_handle_robots(False)
        cookies = mechanize.CookieJar()
        self.set_cookiejar(cookies)
        self.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.41 Safari/534.7')]
        self.set_handle_refresh(False)
        self.open(f"{host}/login")
        self.select_form(nr = 0)
        self.form['login'] = username
        self.form['password'] = password
        self.submit()
        # pylint: enable=no-member

    def scrape_user_email(self, username):
        url = f"{self.host}/stafftools/users/{username}"
        try:
            # pylint: disable=assignment-from-none
            resp = self.open(url)
            # pylint: enable=assignment-from-none
            content = resp.read()
            soup = bs(content, 'html.parser')
            email = soup.find("ul", {"class": 'site-admin-detail-list'}).findAll('li')[1].getText().strip().split("\n")[0]
            if "@" in email:
                return email
        except mechanize._response.HTTPError as e:
            self.log.error(f"{e}: {url}")
            return None
        