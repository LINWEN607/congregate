import requests
import re
import os

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

    def generate_request_url(self, api):
        return f"{self.config.source_host}/{api}"
    
    @stable_retry
    def generate_get_request(self, api, params=None, description=None):
        """
        Generates GET request to ADO API.
        You will need to provide the access token, and specific api url.

            :param token: (str) Access token to ADO instance
            :param api: (str) Specific ADO API endpoint (ex: projects)
            :param url: (str) A URL to a location not part of the ADO API. Defaults to None
            :param params:
            :return: The response object *not* the json() or text()
        """

        url = self.generate_request_url(api)
        audit.info(generate_audit_log_message("GET", description, url))
        headers = self._get_headers()
        if params:
            params['api-version'] = self.config.ado_api_version
        else:
            params = {'api-version': self.config.ado_api_version}
        return requests.get(url, params=(params or {}), headers=headers, verify=self.config.ssl_verify)

    @stable_retry
    def generate_post_request(self, api, data, description=None):
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

        return requests.post(url, data=data, headers=headers, verify=self.config.ssl_verify)

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


    def list_all(self, api, params=None):
        """
        Generates a list of all projects, groups, users, etc.

            :param api: (str) Specific ADO API endpoint (ex: users)
            :param params: (str) Any query parameters needed in the request
            :yields: Individual objects from the presumed array of data    
        """

        while True:
            response = self.generate_get_request(api, params=params)
            response.raise_for_status()
            data = safe_json_response(response)
            for item in data.get("value", []):
                yield item

            if "x-ms-continuationtoken" not in response.headers:
                break

            params["continuationToken"] = response.headers["x-ms-continuationtoken"]


    def get_count(self, api, params=None):
        """
        Generates a count of all projects, groups, users, etc.
        
            :param api: (str) Specific ADO API endpoint (ex: users)
            :param params: (str) Any query parameters needed in the request
            :return: (int) Count of objects in the presumed array of data
        """

        response = self.generate_get_request(api, params=params)
        return response.json().get("count", 0)


    def slugify(self, text):
        return re.sub(r'\s+', '-', re.sub(r'[^\w\s-]', '', text.lower())).strip('-')
    

    def format_project(self, project, repository, count, mongo):
        self.project_groups = {}
        path_with_namespace = self.slugify(project["name"])
        if count > 1:
            path_with_namespace = os.path.join(self.slugify(project["name"]), self.slugify(repository["name"]))

        return {
            "name": repository["name"],
            "id": repository["id"],
            "path": self.slugify(repository["name"]),
            "path_with_namespace": path_with_namespace,
            "visibility": project["visibility"],
            "description": project.get("description", ""),
            "members": [],
            "projects": [],
            "http_url_to_repo": repository["remoteUrl"],
            "ssh_url_to_repo": repository["sshUrl"]
        }

    def format_group(self, project, mongo):
        self.project_groups = {}
        return {
            "name": project["name"],
            "id": project["id"],
            "path": self.slugify(project["name"]),
            "full_path": self.slugify(project["name"]),
            "visibility": project["visibility"],
            "description": project.get("description", ""),
            "members": [],
            "projects": []
        }
