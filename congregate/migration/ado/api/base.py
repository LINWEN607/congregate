from urllib.parse import urljoin
import requests
import sys

from congregate.helpers.base_class import BaseClass
from gitlab_ps_utils.decorators import stable_retry
from gitlab_ps_utils.audit_logger import audit_logger
from gitlab_ps_utils.logger import myLogger
from gitlab_ps_utils.misc_utils import generate_audit_log_message, safe_json_response

log = myLogger(__name__)
audit = audit_logger(__name__)


class AzureDevOpsApiWrapper(BaseClass):
    def _get_headers(self):
        return {
            "Authorization": f"Basic {self.config.source_token}",
            "Content-Type": "application/json"
        }

    def generate_request_url(self, api, sub_api=None):
        base_url = self.config.source_host
        if not (base_url.startswith("https://") or base_url.startswith("http://")):
            print("Invalid URL. Please provide a valid URL.")
            sys.exit(1)
        if sub_api and "dev.azure.com" in base_url:
            base_url_parts = base_url.split("://", 1)
            base_url = f"{base_url_parts[0]}://{sub_api}.{base_url_parts[1]}"
        return urljoin(base_url + '/', api)

    @stable_retry
    def generate_get_request(self, api, sub_api=None, params=None, description=None):
        """
        Generates GET request to ADO API.
        You will need to provide the access token, and specific api url.

            :param token: (str) Access token to ADO instance
            :param api: (str) Specific ADO API endpoint (ex: projects)
            :param url: (str) A URL to a location not part of the ADO API. Defaults to None
            :param params:
            :return: The response object *not* the json() or text()
        """

        url = self.generate_request_url(api, sub_api)
        audit.info(generate_audit_log_message("GET", description, url))
        headers = self._get_headers()
        if params:
            params['api-version'] = self.config.ado_api_version
        else:
            params = {'api-version': self.config.ado_api_version}
        return requests.get(url, params=(params or {}), headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_post_request(self, api, data, description=None, params=None):
        """
        Generates POST request to ADO API.
        You will need to provide the access token, and specific api url.

            :param token: (str) Access token to ADO instance
            :param api: (str) Specific ADO API endpoint (ex: projects)
            :param url: (str) A URL to a location not part of the ADO API. Defaults to None
            :param data: (dict) Data to be posted
            :return: The response object *not* the json() or text()
        """

        url = self.generate_request_url(api)
        audit.info(generate_audit_log_message("POST", description, url))

        headers = self._get_headers()
        headers['Content-Type'] = 'application/json'
        if params:
            params['api-version'] = self.config.ado_api_version
        else:
            params = {'api-version': self.config.ado_api_version}

        return requests.post(url, params=(params or {}), data=data, headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_patch_request(self, api, data, description=None):
        """
        Generates PATCH request to ADO API.
        You will need to provide the access token, and specific api url.

            :param token: (str) Access token to ADO instance
            :param api: (str) Specific ADO API endpoint (ex: projects)
            :param url: (str) A URL to a location not part of the ADO API. Defaults to None
            :param data: (dict) Data to be posted
            :return: The response object *not* the json() or text()
        """

        url = self.generate_request_url(api)
        audit.info(generate_audit_log_message("PATCH", description, url))
        headers = self._get_headers()
        return requests.patch(url, data=data, headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_put_request(self, api, data, description=None):
        """
        Generates PUT request to ADO API.
        You will need to provide the access token, and specific api url.

            :param token: (str) Access token to ADO instance
            :param api: (str)
            :param url: (str) A URL to a location not part of the ADO API. Defaults to None
            :param data: (dict) Data to be posted
            :return: The response object *not* the json() or text()
        """

        url = self.generate_request_url(api)
        audit.info(generate_audit_log_message("PUT", description, url))
        headers = self._get_headers()
        return requests.put(url, data=data, headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_delete_request(self, api, description=None):
        """
        Generates DELETE request to ADO API.
        You will need to provide the access token, and specific api url.

            :param token: (str) Access token to ADO instance
            :param api: (str) Specific ADO API endpoint (ex: projects)
            :param url: (str) A URL to a location not part of the ADO API. Defaults to None
            :return: The response object *not* the json() or text()
        """

        url = self.generate_request_url(api)
        audit.info(generate_audit_log_message("DELETE", description, url))
        headers = self._get_headers()
        return requests.delete(url, headers=headers, verify=self.config.ssl_verify)

    def list_all(self, api, params=None, sub_api=None):
        """
        Generates a list of all projects, groups, etc.

            :param api: (str) Specific ADO API endpoint (ex: projects)
            :param params: (str) Any query parameters needed in the request
            :yields: Individual objects from the presumed array of data
        """

        while True:
            response = self.generate_get_request(api, sub_api, params=params)
            response.raise_for_status()
            if data := safe_json_response(response):
                for item in data.get("value", []):
                    yield item
                for item in data.get("members", []):
                    yield item

            if params is None:
                params = {}

            if not any(key.lower() == "x-ms-continuationtoken" for key in response.headers):
                break

            params["continuationToken"] = response.headers["X-MS-ContinuationToken"]

    def list_all_in_tfs(self, api, params=None, sub_api=None):
        """
        Generates a list of all projects, groups, etc., or all items using $top/$skip paging.

            :param api: (str) Specific ADO API endpoint (ex: projects)
            :param params: (dict) Any query parameters needed in the request
            :yields: Individual objects from the presumed array of data
        """
        # If params is None, initialize as empty dict
        if params is None:
            params = {}

        # If $top is specified, use $skip/$top paging logic
        if "$top" in params:
            skip = params.get("$skip", 0)
            top = params["$top"]
            while True:
                params["$skip"] = skip
                response = self.generate_get_request(api, sub_api, params=params)
                response.raise_for_status()
                data = safe_json_response(response)
                items = []
                if data:
                    items = data.get("value", []) or data.get("members", [])
                    for item in items:
                        yield item
                if not items:
                    break
                skip += top
        else:
            # Fallback to continuation token logic
            while True:
                response = self.generate_get_request(api, sub_api, params=params)
                response.raise_for_status()
                data = safe_json_response(response)
                if data:
                    for item in data.get("value", []):
                        yield item
                    for item in data.get("members", []):
                        yield item

                if not any(key.lower() == "x-ms-continuationtoken" for key in response.headers):
                    break

                params["continuationToken"] = response.headers["X-MS-ContinuationToken"]

    def get_count(self, api, params=None):
        """
        Generates a count of all projects, groups, users, etc.

            :param api: (str) Specific ADO API endpoint (ex: users)
            :param params: (str) Any query parameters needed in the request
            :return: (int) Count of objects in the presumed array of data
        """

        response = self.generate_get_request(api, sub_api=None, params=params)
        return response.json().get("count", 0)
