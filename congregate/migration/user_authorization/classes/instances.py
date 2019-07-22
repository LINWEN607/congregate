import requests
import json
from ..util.misc import stable_retry

class Instance(object):

    def __init__(self, api_url_base):
        self.api_url_base = api_url_base

    @property
    def api_url_base(self):
        return self._api_url_base

    @api_url_base.setter
    def api_url_base(self, api_url_base):
        self._api_url_base = api_url_base if api_url_base[-1] != '/' else api_url_base[:-1]

    @stable_retry
    def api_request(self, request_type, url_extension='', params=None, api_headers=None, auth=None, data=None):
        request_function_map = {
            'get': requests.get,
            'post': requests.post,
            'put': requests.put
        }
        if params == None and hasattr(self, 'params'):
            params = self.params
        if auth == None and hasattr(self, 'auth'):
            auth = self.auth
        if api_headers == None and hasattr(self, 'api_headers'):
            api_headers = self.api_headers
        if data == None and hasattr(self, 'data'):
            data = self.data
        if data != None:
            data = json.dumps(data)
        url_extension = self.format_url_extension(url_extension=url_extension)
        api_url = self.construct_api_url(api_url_base=self.api_url_base, url_extension=url_extension)
        response = request_function_map[request_type](api_url, params=params, headers=api_headers, auth=auth, data=data)
        return response


    @staticmethod
    def format_url_extension(url_extension):
        url_extension = url_extension if url_extension[0] == '/' else '/' + url_extension
        url_extension = url_extension.replace('//', '/')
        return url_extension

    @staticmethod
    def construct_api_url(api_url_base, url_extension):
        api_url = api_url_base + url_extension
        return api_url


class Gitlab_Instance(Instance):
    def __init__(self, api_url_base):
        Instance.__init__(self, api_url_base)
        self.api_headers = self.get_api_headers()

    def get_api_headers(self):
        headers = {
            "Private-Token": "wfyLWXZrvbBXwnVAYsqb",
            "Content-Type": "application/json"
        }
        return headers


class Bitbucket_Instance(Instance):

    def __init__(self, api_url_base, username, password, **kwargs):
        Instance.__init__(self, api_url_base)
        self.username = username
        self.password = password
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.auth = (self.username, self.password)

    def api_request(self, request_type, url_extension='', params={}, api_headers=None, auth=None, data=None):
        if request_type == 'get':
            params_to_add ={"start": 0, "limit": 1000}
            for k, v in params_to_add.items():
                params[k] = v
        return super(Bitbucket_Instance, self).api_request(request_type, url_extension, params, api_headers, auth, data)