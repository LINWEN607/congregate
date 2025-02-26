import os
import sys
import requests
from json import dumps as json_dumps
from urllib.parse import urljoin
from gitlab_ps_utils.decorators import stable_retry
from gitlab_ps_utils.logger import myLogger
from gitlab_ps_utils.misc_utils import safe_json_response
from congregate.migration.gitlab.api.users import UsersApi


class token_generator():
    def __init__(self):
        self.log = myLogger(__name__)
        self.endpoint = os.getenv('GITLAB_URL')
        self.login = os.getenv('GITLAB_ADMIN_USER')
        self.password = os.getenv('GITLAB_ADMIN_PASSWD')
    
    @stable_retry(retries=50, delay=10)
    def generate_oauth_token(self, url=None, username=None, pword=None):
        if url is not None:
            self.__set_endpoint(url)
        if username is not None:
            self.__set_login(username)
        if pword is not None:
            self.__set_password(pword)
        data = {
            "grant_type": "password",
            "username": self.login,
            "password": self.password
        }
        r = requests.post(self.__get_oauth_token_route(), data=data)
        print(r.text)
        if r.status_code != 200:
            raise Exception(f"Response code expected was 200. Actual was {r.status_code} with response text of {r.text}")
        if response := safe_json_response(r):
            return response.get('access_token')
    
    def generate_pat_from_oauth_token(self, url=None, username=None, pword=None):
        self.log.info(f"Obtaining OAuth Token for {url}")
        oauth_token = self.generate_oauth_token(url=url, username=username, pword=pword)
        self.log.info(f"Obtained OAuth Token for {url}")
        headers = {
            'Authorization': f"Bearer {oauth_token}"
        }
        data = {
            'name': 'congregate',
            'scopes': 'api'
        }
        current_user_id = self.get_current_user_id(oauth_token)
        self.log.info(f"Obtaining PAT for {url}")
        if response := safe_json_response(requests.post(self.__get_pat_api_route(current_user_id), headers=headers, data=data)):
            self.log.info(f"Obtained PAT for {url}")
            return response.get('token')
        sys.exit('Unable to generate PAT from OAuth token and proceed with end to end test. Exiting')

    def generate_group_access_owner_token(self, host, token, group_id):
        headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json'
        }
        data = {
            'name': 'congregate',
            'scopes': ['api'],
            'access_level': 50,
            'expires_at': "2025-12-31 00:00:00"
        }
        new_token = requests.post(urljoin(host, f'/api/v4/groups/{group_id}/access_tokens'), headers=headers, data=json_dumps(data))
        if r := safe_json_response(new_token):
            self.log.info(f"Obtained Group Access Token")
            return r.get('token')
        sys.exit(f'Unable to generate Group Access Token from PAT and proceed with end to end test. The resopnse returned was \n{new_token.text}\n Exiting')
        

    def get_current_user_id(self, token):
        headers = {
            'Authorization': f"Bearer {token}"
        }
        if current_user := safe_json_response(UsersApi().get_current_user(self.endpoint, None, headers=headers)):
            return current_user.get('id')

    def __set_endpoint(self, endpoint):
        self.endpoint = endpoint

    def __set_login(self, login):
        self.login = login

    def __set_password(self, password):
        self.password = password

    def __get_oauth_token_route(self):
        return urljoin(self.endpoint, "/oauth/token")
    
    def __get_pat_api_route(self, user_id):
        return urljoin(self.endpoint, f'/api/v4/users/{user_id}/personal_access_tokens')
