import requests
from bs4 import BeautifulSoup as bs
from congregate.helpers.base_class import BaseClass


class GitHubBrowser(BaseClass):
    def __init__(self, host, username, password):
        super(GitHubBrowser, self).__init__()
        self.host = host
        self.username = username
        self.session = requests.Session()
        res = self.session.get(host, verify=self.config.ssl_verify)
        authenticity_token = self.find_authenticity_token(res.text)
        cookies = dict(res.cookies)
        payload = {
            "login": username,
            "password": password,
            "commit": "Sign in",
            "authenticity_token": authenticity_token
        }
        self.session.post(f"{host}/session", cookies=cookies,
                          data=payload, verify=self.config.ssl_verify)
        self.valid_access = True
        self.valid_access = self.validate_access()

    def find_authenticity_token(self, text):
        soup = bs(text, "lxml")
        token = soup.find(attrs={"name": "authenticity_token"})
        return token.get("value")

    def validate_access(self):
        if self.scrape_user_email(self.username):
            return True
        else:
            self.log.warning(
                "Insufficient access permissions to scrape user email. Skipping.")

    def scrape_user_email(self, username):
        if self.valid_access:
            url = f"{self.host}/stafftools/users/{username}"
            resp = self.session.get(url, verify=self.config.ssl_verify)
            if resp.status_code == 200:
                soup = bs(resp.text, 'html.parser')
                if site_admin_detail_list := soup.find("ul", {"class": 'site-admin-detail-list'}):
                    try:
                        email = site_admin_detail_list.find_all(
                            'li')[1].getText().strip().split("\n")[0]
                        if "@" in email:
                            return email
                    except Exception:
                        return None
