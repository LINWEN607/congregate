import requests
import urllib3

from congregate.helpers.decorators import stable_retry
from congregate.helpers.audit_logger import audit_logger
from congregate.helpers.logger import myLogger


log = myLogger(__name__)
audit = audit_logger(__name__)

# TODO: Remove for production use, together with verify=False in api/orgs.py
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GitHubApi():
    def __init__(self, host, token, query=None, api=None):
        self.host = host
        self.token = token
        self.api = api

        # Test Query
        self.query = """
            query {
            viewer {
                __schema
            }
            }
            """

    def do_all_graphql(self):
        """
        This runs all the required pieces of the class for the V4 GraphQL API
        """
        pass

    def do_all_rest(self):
        """
        This runs all the required pieces of the class for the V3 REST API
        """
        self.generate_v3_get_request(host=self.host, api=self.api)

    def __generate_v3_request_header(self, token):
        """
        Given a token return a dictionary for authorization. Works for REST

        Doc: https://docs.github.com/en/rest/overview/media-types#request-specific-version
        """
        header = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": 'token {}'.format(token)
        }
        return header

    def __generate_v4_request_header(self, token):
        """
        Given a token return a dictionary for authorization. Works for GraphQL

        Doc: https://docs.github.com/en/graphql/guides/forming-calls-with-graphql#authenticating-with-graphql
        """
        header = {
            "Authorization": 'Bearer {}'.format(token)
        }
        return header

    def __generate_v4_request_url(self, host):
        """
        Given a host return a formatted url string for GraphQL
        """
        if host[-1] == "/":
            host = host.rstrip("/")
        return "{}/api/graphql".format(host)

    def __generate_v3_request_url(self, host, api):
        "Create the REST URL for a given host and api end point."
        if host[-1] == "/":
            host = host.rstrip("/")
        return "{}/api/v3/{}".format(host, api)

    def create_v4_query(self, query):
        """
        Given a query string, return a json version of it.
        """
        pass

    @stable_retry
    def generate_v3_get_request(self, host, api, url=None, params=None, verify=True):
        """
        Generate a REST request object
        """
        if url is None:
            url = self.__generate_v3_request_url(host, api)

        headers = self.__generate_v3_request_header(self.token)
        if params is None:
            params = {}
        return requests.get(url, params=params, headers=headers, verify=verify)

    @stable_retry
    def run_v4_query(self, url=None, headers=None, verify=True):
        """
        """
        if not url:
            url = self.__generate_v4_request_url(self.host)
        if not headers:
            headers = self.__generate_v4_request_header(self.token)
        return requests.post(url, json={'query': self.query}, headers=headers, verify=verify)

    def __replace_unwanted_characters(self, s):
        """
        Given string s, remove undesirable characters from it
        """
        remove = [' ', '>', '<', '"']
        for character in remove:
            s = s.replace(character, "")
        return s

    def __create_dict_from_headers(self, headers):
        """
        Given a "Link" kv, return it as a cleaned up dictionary.
        """
        urls = headers.split(",")
        kv = {}

        for r in range(0, len(urls)):
            # get rid of superflous characters
            urls[r] = self.__replace_unwanted_characters(urls[r])
            # split the strings even further
            kvp = urls[r].split(";")
            # get rid of the rel="next" to just be next
            kvp[1] = kvp[1].split("=")[1]
            # add our header dictionary to a list
            kv[kvp[1]] = kvp[0]
        return kv

    def list_all(self, host, api, params=None, limit=1000, verify=True):
        """
        Implement pagination
        """
        isLastPage = False
        log.info("Listing endpoint: {}".format(api))
        url = self.__generate_v3_request_url(host, api)
        data = []
        while isLastPage is False:
            if not params:
                params = {
                    "per_page": limit
                }
            else:
                params["per_page"] = limit
            r = self.generate_v3_get_request(
                host, api, url, params=params, verify=verify)

            if r.status_code != 200:
                if r.status_code == 404 or r.status_code == 500 or r.status_code == 401:
                    log.error('\nERROR: HTTP Response was {}\n\nBody Text: {}\n'.format(
                        r.status_code, r.text))
                    break
                raise ValueError('ERROR HTTP Response was NOT 200, which implies something wrong. The actual return code was {}\n{}\n'.format(
                    r.status_code, r.text))
            # try:
            if r.json() and r.headers.get("Link", None):
                data.extend(r.json())
                h = self.__create_dict_from_headers(r.headers['Link'])
                url = h['next']
            else:
                data.extend(r.json())
                isLastPage = True
                return data
