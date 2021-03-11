#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Borrowed and slightly improved from https://gist.github.com/vitalyisaev2/215f890e75252cd36794221c2debf365
Script creates an 'admin' Personal Access Token for Gitlab API.
It spits out the token
Tested with GitLab Community Edition 10.8.4
Example: ./<script> <name-of-token> <expiry>
./<script> mytoken 2020-08-27
## Requirements :-
1) Python3
2) Sript needs below environment variables to be setup:
  - GITLAB_URL='http://<IP>:<port>'
  - GITLAB_ADMIN_USER='root'
  - GITLAB_ADMIN_PASSWD='5iveL!fe'
TO-DO:
A lot of improvements can be done on this script, will do that as time permits. Few of those are :-
- Use argparse to have arguments
- Parameterize Scopes - api, read_user, sudo, read_repository
- Convert this into a GoLang script to remove the dependencies and reduce the footprint of docker image
"""

# Import Modules
import os
import sys
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from congregate.helpers.decorators import configurable_stable_retry
from congregate.helpers.logger import myLogger


class token_generator():
    def __init__(self):
        self.log = myLogger(__name__)
        self.endpoint = os.getenv('GITLAB_URL')
        self.login = os.getenv('GITLAB_ADMIN_USER')
        self.password = os.getenv('GITLAB_ADMIN_PASSWD')
        self.scopes = {'personal_access_token[scopes][]': [
            'api', 'sudo', 'read_user', 'read_repository']}

    # Methods
    def find_csrf_token(self, text):
        soup = BeautifulSoup(text, "lxml")
        token = soup.find(attrs={"name": "csrf-token"})
        param = soup.find(attrs={"name": "csrf-param"})
        data = {param.get("content"): token.get("content")}
        return data

    @configurable_stable_retry(retries=50, delay=10)
    def obtain_csrf_token(self):
        self.log.info("Obtaining CSRF token")
        r = requests.get(self.__get_root_route())
        self.log.debug(f"Status code for {self.__get_root_route}: {r.status_code}")
        if r.status_code != 200:
            raise Exception
        token = self.find_csrf_token(r.text)
        reset_password_token = None
        if "?reset_password_token=" in r.url:
            reset_password_token = r.url.split("?reset_password_token=")[1]
        self.log.info("Found reset password token")
        return token, r.cookies, reset_password_token

    def sign_in(self, csrf, cookies):
        self.log.info("Signing in to GitLab instance")
        data = {
            "user[login]": self.login,
            "user[password]": self.password,
            "user[remember_me]": 0,
            "utf8": "✓"
        }
        data.update(csrf)
        r = requests.post(self.__get_sign_in_route(),
                          data=data, cookies=cookies)
        self.log.debug(f"Status code for {self.__get_sign_in_route()}: {r.status_code}")
        token = self.find_csrf_token(r.text)
        self.log.info("Signed in to GitLab instance")
        if len(r.history) > 0:
            return token, r.history[0].cookies
        return token, cookies

    def change_password(self, csrf, cookies, reset_password_token):
        if reset_password_token is not None:
            self.log.info("Changing password for root")
            data = {
                "utf8": "✓",
                "_method": "put",
                "user[password]": self.password,
                "user[password_confirmation]": self.password,
                "user[reset_password_token]": reset_password_token,
            }
            data.update(csrf)
            r = requests.post(self.__get_password_route(),
                              data=data, cookies=cookies)
            self.log.debug(f"Status code for {self.__get_password_route()}: {r.status_code}")
            token = self.find_csrf_token(r.text)
            if len(r.history) > 0:
                return token, r.history[0].cookies
            return token, cookies
        self.log.info("Reset password token was None. Not changing password")
        return csrf, cookies

    def obtain_personal_access_token(self, name, expires_at, csrf, cookies):
        self.log.info("Obtaining personal access token for root")
        data = {
            "personal_access_token[expires_at]": expires_at,
            "personal_access_token[name]": name,
            "utf8": "✓"
        }
        data.update(self.scopes)
        data.update(csrf)
        r = requests.post(self.__get_pat_route(), data=data, cookies=cookies)
        self.log.debug(f"Status code for {self.__get_pat_route()}: {r.status_code}")
        if r.status_code != 200:
            r = requests.post(urljoin(self.endpoint, "/profile/personal_access_tokens"), data=data, cookies=cookies)
            self.log.debug(f"Status code for {self.__get_pat_route()}: {r.status_code}")
        soup = BeautifulSoup(r.text, "lxml")
        token = soup.find(
            'input', id='created-personal-access-token').get('value')
        self.log.info("Obtained personal access token for root")
        return token

    def generate_token(self, name, expires_at, url=None, username=None, pword=None):
        if url is not None:
            self.__set_endpoint(url)
        if username is not None:
            self.__set_login(username)
        if pword is not None:
            self.__set_password(pword)

        csrf1, cookies1, reset_password_token = self.obtain_csrf_token()
        if reset_password_token is not None:
            csrf2, cookies2 = self.change_password(
                csrf1, cookies1, reset_password_token)
            csrf3, cookies3 = self.sign_in(csrf2, cookies2)
        else:
            csrf3, cookies3 = self.sign_in(csrf1, cookies1)

        token = self.obtain_personal_access_token(
            name, expires_at, csrf3, cookies3)

        self.log.info("Token has been successfully generated")
        return token

    def __set_endpoint(self, endpoint):
        self.endpoint = endpoint

    def __set_login(self, login):
        self.login = login

    def __set_password(self, password):
        self.password = password

    def __get_root_route(self):
        return urljoin(self.endpoint, "/")

    def __get_sign_in_route(self):
        return urljoin(self.endpoint, "/users/sign_in")

    def __get_password_route(self):
        return urljoin(self.endpoint, "/users/password")

    def __get_pat_route(self):
        return urljoin(self.endpoint, "/-/profile/personal_access_tokens")


if __name__ == "__main__":
    t = token_generator()
    name_arg = sys.argv[1]
    expires_at_arg = sys.argv[2]
    log = myLogger(__name__)
    log.info(t.generate_token(name_arg, expires_at_arg))
