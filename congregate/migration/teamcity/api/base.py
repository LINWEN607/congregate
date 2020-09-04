import requests
import json
from requests.auth import HTTPBasicAuth
from congregate.helpers.misc_utils import xml_to_dict
from congregate.helpers.decorators import stable_retry
from congregate.helpers.logger import myLogger


class TeamcityApi():
    def __init__(self, host, user, token):
        self.log = myLogger(__name__)
        self.host = host
        self.token = token
        self.user = user

    def generate_tc_request_url(self, host, api):
        return "%s/app/rest/%s" % (host, api)

    def generate_request_headers(self):
        return {
            'Content-Type': 'application/json'
        }

    def get_authorization(self):
        return HTTPBasicAuth(self.user, self.token)

    @stable_retry
    def generate_get_request(self, api, url=None, params=None):
        """
        Generates GET request to TeamCity API.
        You will need to provide the TC host, user, access token, and specific api url.

            :param host: (str) TeamCity host URL
            :param api: (str) Specific TeamCity API endpoint (ex: buildTypes)
            :param url: (str) A URL to a location not part of the TeamCity API. Defaults to None
            :param params:
            :return: The response object *not* the json() or text()

        """

        if url is None:
            url = self.generate_tc_request_url(self.host, api)

        headers = self.generate_request_headers()

        if params is None:
            params = {}

        auth = self.get_authorization()
        return requests.get(url, params=params, headers=headers, auth=auth)

    def list_build_configs(self):
        """
        Returns a dictionary of list of all build configurations on the TeamCity server.
        """
        return xml_to_dict(self.generate_get_request("buildTypes").text)

    def get_build_config(self, jobid):
        """
        Returns a dictionary of a specific build configuration on the TeamCity server.
        """
        return xml_to_dict(self.generate_get_request("buildTypes/%s" % jobid).text)

    def get_build_params(self, jobid):
        """
        Returns a dictionary of parameters to a specific build configuration on the TeamCity server.
        """
        return xml_to_dict(self.generate_get_request("buildTypes/%s/parameters" % jobid).text)

    def list_build_params(self, jobid):
        """
        Returns a list of paramaters to a specific build configuration on the TeamCity server.
        """
        job_data = self.get_build_params(jobid)
        param_list = []

        for param in job_data["properties"]["property"]:
            param_list.append(param)

        return param_list

    def get_build_vcs_roots(self, jobid):
        """
        Returns a dictionary of vcs entries to a specific build configuration on the TeamCity server.
        """
        job_data = self.get_build_config(jobid)
        if "vcs-root-entry" in job_data["buildType"]["vcs-root-entries"]:
            vcs_id = job_data["buildType"]["vcs-root-entries"]["vcs-root-entry"]["@id"]
        else:
            return "no_scm"
        return xml_to_dict(self.generate_get_request("vcs-roots/%s" % vcs_id).text)

    def list_vcs_configs(self):
        """
        Returns a dictionary of list of all vcs roots on the TeamCity server.
        """
        return xml_to_dict(self.generate_get_request("vcs-roots").text)
