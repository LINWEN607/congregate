from time import sleep
from base64 import b64encode
import requests

from gitlab_ps_utils.decorators import stable_retry
from gitlab_ps_utils.misc_utils import generate_audit_log_message
from congregate.helpers.base_class import BaseClass


class BitBucketServerApi(BaseClass):

    def generate_bb_v1_request_url(self, api, branch_permissions=False):
        if branch_permissions:
            return f"{self.config.source_host}/rest/branch-permissions/2.0/{api}"
        return f"{self.config.source_host}/rest/api/1.0/{api}"

    def generate_v4_request_headers(self, branch_permissions=False):
        auth = f"{self.config.source_username}:{self.config.source_token}".encode(
            "ascii")
        return {
            # For bulk POST or single GET/POST/DELETE requests
            "Content-Type": "application/vnd.atl.bitbucket.bulk+json" if branch_permissions else "application/json",
            "Authorization": f"Basic {b64encode(auth).decode('ascii')}"
        }

    @stable_retry
    def generate_get_request(self, api, url=None, params=None, branch_permissions=False):
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
            url = self.generate_bb_v1_request_url(
                api, branch_permissions=branch_permissions)

        headers = self.generate_v4_request_headers()

        return requests.get(url, params=(params or {}), headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_post_request(self, api, data, url=None, branch_permissions=False, description=None):
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
            url = self.generate_bb_v1_request_url(
                api, branch_permissions=branch_permissions)

        self.audit.info(generate_audit_log_message("POST", description, url))
        headers = self.generate_v4_request_headers(
            branch_permissions=branch_permissions)

        return requests.post(url, json=data, headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_put_request(self, api, data, url=None, branch_permissions=False, description=None):
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
            url = self.generate_bb_v1_request_url(
                api, branch_permissions=branch_permissions)

        self.audit.info(generate_audit_log_message("PUT", description, url))
        headers = self.generate_v4_request_headers(
            branch_permissions=branch_permissions)

        return requests.put(url, json=data, headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_delete_request(self, api, url=None, branch_permissions=False, description=None):
        """
        Generates DELETE request to BitBucket API.
        You will need to provide the access token, and specific api url.

            :param token: (str) Access token to BitBucket instance
            :param api: (str) Specific BitBucket API endpoint (ex: projects)
            :param url: (str) A URL to a location not part of the BitBucket API. Defaults to None
            :return: The response object *not* the json() or text()
        """
        if url is None:
            url = self.generate_bb_v1_request_url(
                api, branch_permissions=branch_permissions)

        self.audit.info(generate_audit_log_message("DELETE", description, url))
        headers = self.generate_v4_request_headers()

        return requests.delete(url, headers=headers, verify=self.config.ssl_verify)

    def list_all(self, api, params=None, limit=1000, branch_permissions=False):
        isLastPage = False
        start = 0
        self.log.info(f"Listing endpoint: {api}")
        while isLastPage is False:
            if not params:
                params = {
                    "start": start,
                    "limit": limit
                }
            else:
                params["start"] = start
                params["limit"] = limit
            r = self.generate_get_request(
                api, params=params, branch_permissions=branch_permissions)
            try:
                data = r.json()
                self.log.info(f"Retrieved {data.get('size')} {api}")
                if r.status_code != 200:
                    if r.status_code in [404, 500]:
                        self.log.error(
                            f"\nERROR: HTTP Response was {r.status_code}\n\nBody Text: {r.text}\n")
                        break
                    raise ValueError(
                        f"ERROR HTTP Response was NOT 200, which implies something wrong. The actual return code was {r.status_code}\n{r.text}\n")
                if data.get("values") is not None:
                    for value in data["values"]:
                        yield value
                    isLastPage = data['isLastPage']
                    if isLastPage is False:
                        start = data['nextPageStart']
                else:
                    isLastPage = True
            except ValueError as e:
                self.log.error(e)
                self.log.error("API Request didn't return JSON")
                # Retry interval is smaller here because it will just retry
                # until it succeeds
                self.log.info("Attempting to retry after 3 seconds")
                sleep(3)
