import requests

from congregate.helpers.decorators import stable_retry
from congregate.helpers.audit_logger import audit_logger
from congregate.helpers.logger import myLogger
from congregate.helpers.misc_utils import generate_audit_log_message, safe_json_response
from congregate.helpers.base_class import BaseClass
from congregate.helpers.conf import Config

base = BaseClass()

log = myLogger(__name__)
audit = audit_logger(__name__)


class GitHubApi():
    def __init__(self, host, token, query=None, api=None):
        self.host = host
        self.token = token
        self.api = api
        self.config = Config()
        # Test Query
        self.query = """
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
        if host[-1] == "/":
            host = host.rstrip("/")
        return f"{host}/api/graphql"

    def generate_v3_request_url(self, host, api):
        """
        Create the REST URL for a given host and api end point.
        """
        if host[-1] == "/":
            host = host.rstrip("/")
        return f"{host}/api/v3/{api}"

    @stable_retry
    def generate_v3_get_request(self, host, api, url=None, params=None):
        """
        Generates GET request to GitHub API
        """
        if url is None:
            url = self.generate_v3_request_url(host, api)

        headers = self.generate_v3_request_header(self.token)
        if params is None:
            params = {}
        return requests.get(url, params=params, headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_v3_post_request(self, host, api, data, headers=None, description=None):
        """
        Generates POST request to GitHub API
        """
        url = self.generate_v3_request_url(host, api)
        audit.info(generate_audit_log_message("POST", description, url))
        if headers is None:
            headers = self.generate_v3_request_header(self.token)
        return requests.post(url, json=data, headers=headers, verify=self.config.ssl_verify)

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
        Implement pagination
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

            log.info(f"Listing endpoint: {url}")
            r = self.generate_v3_get_request(
                host, api, url, params=params)
            resp_json = safe_json_response(r)
            if r.status_code != 200:
                if r.status_code == 404 or r.status_code == 500 or r.status_code == 401:
                    log.error(
                        f"\nERROR: HTTP Response was {r.status_code}\n\nBody Text: {r.text}\n")
                    break
                yield ValueError(
                    f"ERROR HTTP Response was NOT 200, which implies something wrong."
                    f"The actual return code was {r.status_code}\n{r.text}\n"
                )
            if resp_json and r.headers.get("Link", None):
                h = self.create_dict_from_headers(r.headers['Link'])
                if h.get('next', None):
                    url = h['next']
                    yield from self.pageless_data(resp_json, page_check=page_check, lastPage=lastPage)
                resp_length = len(resp_json)
                if resp_length < limit:
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


    def pageless_data(self, resp_json, page_check=False, lastPage=None):
        if isinstance(resp_json, list):
            if resp_json:
                for data in resp_json:
                    yield (data, lastPage) if page_check else data
        else:
            yield (resp_json, lastPage) if page_check else resp_json