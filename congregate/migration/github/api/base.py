import requests
from gitlab_ps_utils.decorators import stable_retry, token_rotate
from gitlab_ps_utils.audit_logger import audit_logger
from gitlab_ps_utils.logger import myLogger
from gitlab_ps_utils.misc_utils import generate_audit_log_message, safe_json_response

from congregate.helpers.utils import is_github_dot_com
from congregate.helpers.base_class import BaseClass
from congregate.helpers.conf import Config

base = BaseClass()

log = myLogger(__name__)
audit = audit_logger(__name__)


class GitHubApi():
    index = 0

    def __init__(self, host, token, query=None, api=None):
        self.host = host
        self.api = api
        self.config = Config()
        self.token_array = self.config.source_token_array
        # Give passed variables priority
        self.token = self.token_array[self.index] if (
            self.token_array and len(self.token_array) > 1) else token
        # Test Query
        self.query = query or """
            query {
            viewer {
                __schema
            }
            }
            """

    def generate_v3_request_header(self, token):
        """
        Given a token return a dictionary for authorization. Works for REST

        Doc: https://docs.github.com/en/rest/overview/media-types#request-specific-version
        """
        header = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}"
        }
        return header

    def generate_v3_basic_auth_request_header(self):
        """
        Some GitHub endpoints can only be used via basic auth (user/pass) and do not accept
        the token header
        """
        header = {
            "Accept": "application/vnd.github.v3+json"
        }
        return header

    def generate_v3_basic_auth(self, username, password):
        """
        Generate the basic auth parameter for a v3 request
        """
        auth = (username, password)
        return auth

    def generate_v4_request_header(self, token):
        """
        Given a token return a dictionary for authorization. Works for GraphQL

        Doc: https://docs.github.com/en/graphql/guides/forming-calls-with-graphql#authenticating-with-graphql
        """
        header = {
            "Authorization": f"Bearer {token}"
        }
        return header

    def generate_v4_request_url(self, host):
        """
        Given a host return a formatted url string for GraphQL
        """
        host = host.rstrip("/")
        return f"{host}/graphql" if is_github_dot_com(
            host) else f"{host}/api/graphql"

    def generate_v3_request_url(self, host, api):
        """
        Create the REST URL for a given host and api end point.
        """
        host = host.rstrip("/")
        return f"{host}/{api}" if is_github_dot_com(
            host) else f"{host}/api/v3/{api}"

    @stable_retry
    @token_rotate
    def generate_v3_get_request(self, host, api, url=None, params=None):
        """
        Generates GET request to GitHub API
        """
        if url is None:
            url = self.generate_v3_request_url(host, api)

        headers = self.generate_v3_request_header(self.token)
        if params is None:
            params = {}
        return requests.get(url, params=params, headers=headers,
                            verify=self.config.ssl_verify)

    @stable_retry
    def generate_v3_basic_auth_get_request(
            self, host, api, username, password, url=None, params=None):
        """
        Generates GET request to GitHub API for a Basic AUTH request
        """
        if url is None:
            url = self.generate_v3_request_url(host, api)

        headers = self.generate_v3_basic_auth_request_header()
        auth = self.generate_v3_basic_auth(username, password)
        if params is None:
            params = {}
        return requests.get(url, params=params, headers=headers,
                            verify=self.config.ssl_verify, auth=auth)

    @stable_retry
    def generate_v3_basic_auth_post_request(
            self, host, api, username, password, data, header=None, description=None):
        """
        Generates POST request to GitHub API for a Basic AUTH request
        """
        url = self.generate_v3_request_url(host, api)
        audit.info(generate_audit_log_message("POST", description, url))
        if header is None:
            headers = self.generate_v3_basic_auth_request_header()
        auth = self.generate_v3_basic_auth(username, password)
        return requests.post(url, json=data, headers=headers,
                             verify=self.config.ssl_verify, auth=auth)

    @stable_retry
    @token_rotate
    def generate_v3_post_request(
            self, host, api, data, headers=None, description=None):
        """
        Generates POST request to GitHub API
        """
        url = self.generate_v3_request_url(host, api)
        audit.info(generate_audit_log_message("POST", description, url))
        if headers is None:
            headers = self.generate_v3_request_header(self.token)
        return requests.post(url, json=data, headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    @token_rotate
    def generate_v3_patch_request(
            self, host, api, data, headers=None, description=None):
        """
        Generates PATCH request to GitHub API
        """
        url = self.generate_v3_request_url(host, api)
        audit.info(generate_audit_log_message("PATCH", description, url))
        if headers is None:
            headers = self.generate_v3_request_header(self.token)
        return requests.patch(url, json=data, headers=headers,
                              verify=self.config.ssl_verify)

    def replace_unwanted_characters(self, s):
        """
        Given string s, remove undesirable characters from it
        """
        remove = [' ', '>', '<', '"']
        for character in remove:
            s = s.replace(character, "")
        return s

    def create_dict_from_headers(self, headers):
        """
        Given a "Link" kv, return it as a cleaned up dictionary.
        """
        urls = headers.split(",")
        kv = {}

        for r in range(0, len(urls)):
            # get rid of superflous characters
            urls[r] = self.replace_unwanted_characters(urls[r])
            # split the strings even further
            kvp = urls[r].split(";")
            # get rid of the rel="next" to just be next
            kvp[1] = kvp[1].split("=")[1]
            # add our header dictionary to a list
            kv[kvp[1]] = kvp[0]
        return kv

    def list_all(self, host, api, params=None, limit=100, page_check=False):
        """
        Generates a list of all projects, groups, users, etc.

        :param host: (str) GitHub host URL
        :param api: (str) Specific GitLab API endpoint (ex: users)
        :param params: (str) Any query parameters needed in the request
        :param limit: (int) Total results per request. Defaults to 100
        :param page_check: (bool) If True, then the yield changes from a dict to a tuple of (dict, bool) where bool is True if list_all has reached the last page

        :yields: Individual objects from the presumed array of data
        """
        url = self.generate_v3_request_url(host, api)
        lastPage = False
        while lastPage is not True:
            if not params:
                params = {
                    "per_page": limit
                }
            else:
                params["per_page"] = limit

            log.info(f"Listing {host} endpoint: {url}")
            r = self.generate_v3_get_request(
                host, api, url, params=params)
            resp_json = safe_json_response(r)
            if r.status_code != 200:
                if r.status_code >= 400:
                    log.error(
                        f"\nERROR: HTTP Response was {r.status_code}.\nBody Text: '{r.text}'")
                    break
                yield (resp_json, True) if page_check else resp_json
            if resp_json and r.headers.get("Link", None):
                h = self.create_dict_from_headers(r.headers['Link'])
                if h.get('next', None):
                    url = h['next']
                    yield from self.pageless_data(resp_json, page_check=page_check, lastPage=lastPage)
                resp_length = len(resp_json)
                if (resp_length < limit) or all(k not in h.keys()
                                                for k in ["next", "last"]):
                    if isinstance(resp_json, list):
                        for i, data in enumerate(resp_json):
                            if i == resp_length - 1:
                                lastPage = True
                            yield (data, lastPage) if page_check else data
                    else:
                        lastPage = True
                        yield from self.pageless_data(resp_json, page_check=page_check, lastPage=lastPage)
            else:
                lastPage = True
                yield from self.pageless_data(resp_json, page_check=page_check, lastPage=lastPage)

    def get_total_count(self, host, api, params=None,
                        limit=100, page_check=False):
        """
        Retrieves total count of records form paginated API call

        :param host: (str) GitHub host URL
        :param api: (str) Specific GitLab API endpoint (ex: users)
        :param params: (str) Any query parameters needed in the request
        :param limit: (int) Total results per request. Defaults to 100
        :param page_check: (bool) If True, then the yield changes from a dict to a tuple of (dict, bool) where bool is True if list_all has reached the last page

        :returns: Total number of records related to that API call
        """
        uniq = {}
        for data in self.list_all(
                host, api, params=params, limit=limit, page_check=page_check):
            # Ignoring any data containing the 'pull_request' key.
            # See
            # https://docs.github.com/en/rest/reference/issues#list-repository-issues
            # for more information
            if 'pull_request' not in data.keys():
                uniq[data.get("id", data.get("name"))] = 1
        count = len(uniq)
        log.info(f"Total count for {host} endpoint {api}: {count}")
        return count

    def pageless_data(self, resp_json, page_check=False, lastPage=False):
        """
        Generator helper function to yield a dictionary or tuple from list_all requests

        :param resp_json: (dict) JSON response from list_all get request
        :param page_check: (bool) If True, then the yield changes from a dict to a tuple of (dict, bool) where bool is True if list_all has reached the last page
        :param lastPage: (bool) Denotes if the data about to be yielded is on the last page

        :yields: Individual objects from resp_json
        """
        if isinstance(resp_json, list):
            if resp_json:
                for data in resp_json:
                    yield (data, lastPage) if page_check else data
        else:
            yield (resp_json, lastPage) if page_check else resp_json
