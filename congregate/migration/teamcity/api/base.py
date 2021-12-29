import requests

from bs4 import BeautifulSoup as bs
from gitlab_ps_utils.dict_utils import xml_to_dict, dig
from gitlab_ps_utils.decorators import stable_retry
from gitlab_ps_utils.logger import myLogger
from congregate.helpers.conf import Config


class TeamcityApi():
    def __init__(self, host, user, token):
        self.log = myLogger(__name__)
        self.host = host
        self.token = token
        self.user = user
        self.config = Config()

    def generate_tc_request_url(self, host, api):
        return "%s/app/rest/%s" % (host, api)

    def generate_request_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.token}"
        }

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

        return requests.get(url, params=params, headers=headers,
                            verify=self.config.ssl_verify)

    def get_maven_settings_file_links(self, jobid, recursive=False):
        t = []
        maven_settings_request = self.generate_get_request(
            None, url=f"{self.host}/admin/editProject.html?projectId={jobid}&tab=mavenSettings")
        if maven_settings_request.status_code == 200:
            data = maven_settings_request.text
            s = bs(data, 'html.parser')
            if table := s.find(id='mavenSettingsTable'):
                for f in table.findAll(class_='edit'):
                    link = f.find('a')['onclick']
                    if "document.location.href" in link:
                        file_link = link.split(
                            "document.location.href = '")[-1].replace("';", "")
                        t.append(file_link)
        else:
            if not recursive:
                reattempt = self.get_maven_settings_file_links(
                    "_".join(jobid.split("_")[:-1]), recursive=True)
                if reattempt:
                    t += reattempt
        return t

    def extract_maven_xml(self, url):
        page = self.generate_get_request(None, url=f"{self.host}/{url}").text
        s = bs(page, 'html.parser')
        try:
            return url.split("&file=")[-1], s.find_all('pre')[0].text
        except Exception as e:
            self.log.error(f"Unable to extract maven xml due to: '{e}'")
            return None, None

    def list_build_configs(self):
        """
        Returns a dictionary of list of all build configurations on the TeamCity server.
        """
        return xml_to_dict(self.generate_get_request("buildTypes").text)

    def get_build_config(self, jobid):
        """
        Returns a dictionary of a specific build configuration on the TeamCity server.
        """
        return self.generate_get_request("buildTypes/%s" % jobid)

    def get_build_params(self, jobid):
        """
        Returns a dictionary of parameters to a specific build configuration on the TeamCity server.
        """
        if param_response := self.generate_get_request(
                "buildTypes/%s/parameters" % jobid):
            return xml_to_dict(param_response.text)

    def list_build_params(self, jobid):
        """
        Returns a list of paramaters to a specific build configuration on the TeamCity server.
        """
        job_data = self.get_build_params(jobid)
        param_list = []

        for param in dig(job_data, 'properties', 'property', default=[]):
            param_list.append(param)

        return param_list

    def get_build_vcs_roots(self, jobid):
        """
        Returns a dictionary of vcs entries to a specific build configuration on the TeamCity server.
        """
        job_data = xml_to_dict(self.get_build_config(jobid).text)
        if "vcs-root-entry" in dig(job_data, 'buildType',
                                   'vcs-root-entries', default=""):
            vcs_id = dig(
                job_data,
                'buildType',
                'vcs-root-entries',
                'vcs-root-entry',
                '@id')
        else:
            return "no_scm"
        return xml_to_dict(self.generate_get_request(
            "vcs-roots/%s" % vcs_id).text)

    def list_vcs_configs(self):
        """
        Returns a dictionary of list of all vcs roots on the TeamCity server.
        """
        return xml_to_dict(self.generate_get_request("vcs-roots").text)
