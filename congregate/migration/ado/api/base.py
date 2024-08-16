import requests
from gitlab_ps_utils.decorators import stable_retry
from congregate.helpers.base_class import BaseClass

class AzureDevOpsClient(BaseClass):

    def _get_headers(self):
        return {
            "Authorization": f"Basic {self.config.source_token}",
            "Content-Type": "application/json"
        }

    def generate_request_url(self, api):
        return f"{self.config.source_host}/{api}"
    
    @stable_retry
    def generate_get_request(self, api, params=None):
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
        headers = self._get_headers()
        if params:
            params['api-version'] = self.config.ado_api_version
        else:
            params = {'api-version': self.config.ado_api_version}

        return requests.get(url, params=(params or {}), headers=headers, verify=self.config.ssl_verify)
