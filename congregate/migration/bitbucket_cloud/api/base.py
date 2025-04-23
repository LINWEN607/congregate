from time import sleep
from base64 import b64encode
import requests

from gitlab_ps_utils.decorators import stable_retry
from gitlab_ps_utils.misc_utils import generate_audit_log_message, safe_json_response
from congregate.helpers.base_class import BaseClass


class BitBucketCloudApi(BaseClass):

    def generate_bb_v2_request_url(self, api, groups_info=False):
        if groups_info:
            return f"{self.config.source_host}/1.0/{api}"
        return f"{self.config.source_host}/2.0/{api}"   # This will always be https://api.bitbucket.org

    def generate_v2_request_headers(self):
        """
        Generate headers for Bitbucket Cloud API requests.
        
        There are two authentication options for Bitbucket Cloud:
        1. OAuth token - use Bearer prefix
        2. Basic Auth with username:app_password - use Basic prefix with base64 encoding
        
        This method handles both cases based on configuration.
        """
        # If username is provided, assume we're using an app password with Basic Auth
        if self.config.source_username:
            auth = f"{self.config.source_username}:{self.config.source_token}".encode("ascii")
            auth_header = f"Basic {b64encode(auth).decode('ascii')}"
        else:
            # Otherwise assume we're using an OAuth token
            auth_header = f"Bearer {self.config.source_token}"
        
        return {
            "Content-Type": "application/json",
            "Authorization": auth_header
        }

    @stable_retry
    def generate_get_request(self, api, url=None, params=None, groups_info=False):
        """
        Generates GET request to BitBucket API.
        You will need to provide the access token, and specific api url.

            :param token: (str) Access token to BitBucket instance
            :param api: (str) Specific BitBucket API endpoint (ex: projects)
            :param url: (str) A URL to a location not part of the BitBucket API. Defaults to None
            :param params:
            :return: The response object *not* the json() or text()
        """

        if url is None:
            url = self.generate_bb_v2_request_url(api, groups_info=groups_info)

        headers = self.generate_v2_request_headers()

        return requests.get(url, params=(params or {}), headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_post_request(self, api, data, url=None, description=None):
        """
        Generates POST request to BitBucket API.
        You will need to provide the access token, and specific api url.

            :param token: (str) Access token to BitBucket instance
            :param api: (str) Specific BitBucket API endpoint (ex: projects)
            :param data: JSON payload
            :param url: (str) A URL to a location not part of the BitBucket API. Defaults to None
            :return: The response object *not* the json() or text()
        """
        if url is None:
            url = self.generate_bb_v2_request_url(api)

        self.audit.info(generate_audit_log_message("POST", description, url))
        headers = self.generate_v2_request_headers()

        return requests.post(url, json=data, headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_put_request(self, api, data, url=None, description=None):
        """
        Generates PUT request to BitBucket API.
        You will need to provide the access token, and specific api url.

            :param token: (str) Access token to BitBucket instance
            :param api: (str) Specific BitBucket API endpoint (ex: projects)
            :param data: JSON payload
            :param url: (str) A URL to a location not part of the BitBucket API. Defaults to None
            :return: The response object *not* the json() or text()
        """
        if url is None:
            url = self.generate_bb_v2_request_url(api)

        self.audit.info(generate_audit_log_message("PUT", description, url))
        headers = self.generate_v2_request_headers()

        return requests.put(url, json=data, headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_delete_request(self, api, url=None, description=None):
        """
        Generates DELETE request to BitBucket API.
        You will need to provide the access token, and specific api url.

            :param token: (str) Access token to BitBucket instance
            :param api: (str) Specific BitBucket API endpoint (ex: projects)
            :param url: (str) A URL to a location not part of the BitBucket API. Defaults to None
            :return: The response object *not* the json() or text()
        """
        if url is None:
            url = self.generate_bb_v2_request_url(api)

        self.audit.info(generate_audit_log_message("DELETE", description, url))
        headers = self.generate_v2_request_headers()

        return requests.delete(url, headers=headers, verify=self.config.ssl_verify)

    def list_all(self, api, params=None, limit=1000):
        if not params:
            params = {
                "limit": limit
            }
        else:
            params["limit"] = limit
        
        self.log.info(f"Listing endpoint: {api}")
        
        # Get the first page
        r = self.generate_get_request(api, params=params)
        
        try:
            data = r.json()
            if r.status_code != 200:
                self.log.error(f"HTTP Response was NOT 200: {r.status_code} - {r.text}")
                return
                
            self.log.info(f"Retrieved {data.get('size', 0)} {api}")
            
            # Check if values is in the response
            if "values" not in data:
                self.log.warning(f"No 'values' found in response for {api}")
                return
                
            # Yield each value from the first page
            for value in data["values"]:
                yield value
                
            # Follow pagination until there are no more pages
            next_url = data.get("next")
            while next_url:
                self.log.info(f"Following pagination to {next_url}")
                r = requests.get(next_url, headers=self.generate_v2_request_headers())
                
                if r.status_code != 200:
                    self.log.error(f"HTTP Response was NOT 200: {r.status_code} - {r.text}")
                    break
                    
                if data := safe_json_response(r):
                
                    # Yield each value from this page
                    for value in data.get("values", []):
                        yield value
                    
                # Get the next page URL
                next_url = data.get("next")
        
        except ValueError as e:
            self.log.error(f"API Request didn't return JSON: {e}")
            self.log.error(f"Response status code: {r.status_code}")
            self.log.error(f"Response headers: {r.headers}")
            self.log.error(f"Response text: {r.text[:500]}...")

    def get_total_count(self, api, params=None, limit=1000):
        """
        Retrieves total count of records form paginated API call

        :param api: (str) Specific GitLab API endpoint (ex: users)
        :param params: (str) Any query parameters needed in the request
        :param limit: (int) Total results per request. Defaults to 100
        :param page_check: (bool) If True, then the yield changes from a dict to a tuple of (dict, bool) where bool is True if list_all has reached the last page

        :returns: Total number of records related to that API call
        """
        uniq = {}
        for data in self.list_all(api, params=params, limit=limit):
            # Ignoring any data containing the 'pull_request' key.
            # See
            # https://docs.github.com/en/rest/reference/issues#list-repository-issues
            # for more information
            if 'pull_request' not in data.keys():
                uniq[data.get("id", data.get("name"))] = 1
        count = len(uniq)
        self.log.info(f"Total count for endpoint {api}: {count}")
        return count
