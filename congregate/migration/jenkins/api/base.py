from re import search
import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPBasicAuth
from gitlab_ps_utils.decorators import stable_retry
from gitlab_ps_utils.misc_utils import safe_json_response
from congregate.helpers.base_class import BaseClass


class JenkinsApi(BaseClass):
    FOLDER_JOB_CLASSES = [
        "com.cloudbees.hudson.plugins.folder.Folder",
        "jenkins.branch.OrganizationFolder"]

    def __init__(self, host, user, token):
        self.host = host
        self.token = token
        self.user = user
        super(JenkinsApi, self).__init__()

    def generate_jenkins_request_url(self, host, api=None, jenkins_path=None):
        if jenkins_path is None:
            return f"{host}/api/{api}"
        elif api == "config.xml":
            return f"{host}/{jenkins_path}/config.xml"
        else:
            return f"{host}/{jenkins_path}/api/{api}"

    def generate_request_headers(self):
        return {
            'Content-Type': 'application/json'
        }

    def get_authorization(self):
        return HTTPBasicAuth(self.user, self.token)

    @stable_retry
    def generate_get_request(
            self, api, jenkins_path=None, url=None, params=None):
        """
        Generates GET request to Jenkins API.
        You will need to provide the TC host, user, access token, and specific api url.

            :param host: (str) Jenkins host URL
            :param api: (str) Specific Jenkins API endpoint (ex: buildTypes)
            :param jenkins_path: (str) Specific Jenkins path i.e. host/job/jobname
            :param url: (str) A URL to a location not part of the Jenkins API. Defaults to None
            :param params:
            :return: The response object *not* the json() or text()

        """

        if url is None:
            url = self.generate_jenkins_request_url(
                self.host, api, jenkins_path)

        headers = self.generate_request_headers()

        if params is None:
            params = {}

        auth = self.get_authorization()
        return requests.get(url, params=params, headers=headers,
                            auth=auth, verify=self.config.ssl_verify)

    def list_all_jobs(self, jobs_path=None, folder_list=None):
        """
        Returns a list of job dictionaries of all jobs found on the Jenkins server.
        """
        self.log.info(f"Listing job {jobs_path} from {self.host}")
        folder_list = set() if not folder_list else folder_list
        if base_data := self.list_current_level_jobs(jobs_path):
            for job in base_data["jobs"]:
                if job not in self.FOLDER_JOB_CLASSES:
                    yield job
                else:
                    if job_path not in folder_list:
                        folder_list.add(job_path)
                        job_path = self.strip_url(job["url"]).rstrip('/')
                        yield from self.list_all_jobs(job_path)
                    else:
                        self.log.info("Duplicate folder found.")
                        raise StopIteration

    def list_current_level_jobs(self, job_path):
        """
        Returns a dict of job dictionaries at provided job_path
        """
        return safe_json_response(self.generate_get_request(
            "json", job_path, None, "pretty&tree=jobs[name,fullName,url,scm[userRemoteConfigs[url]]]"))

    def get_job_config_xml(self, job_path):
        """
        Returns the xml of a specific job configuration on the Jenkins server.
        """
        return self.safe_response(
            self.generate_get_request("config.xml", job_path))

    def get_job_params(self, job_path):
        '''
        Parameters:	job_path - Path to Jenkins job, str
        Returns:    list of param dictionaries in following format
            [{"name": param_name}, {"defaultValue": param_value}]
        '''
        job_info = safe_json_response(
            self.generate_get_request(
                "json", job_path))

        param_list = []
        if job_info:
            job_properties = job_info.get("property", [])

            for dictionary in job_properties:
                if dictionary.get("parameterDefinitions"):
                    for param_data in dictionary["parameterDefinitions"]:
                        if param_data.get("defaultParameterValue"):
                            param_list.append(
                                {"name": param_data["name"], "defaultValue": param_data["defaultParameterValue"].get("value")})
                        else:
                            param_list.append(
                                {"name": param_data["name"], "defaultValue": None})

        return param_list

    def get_scm(self, job_path):
        '''
        https://docs.python.org/2/library/xml.etree.elementtree.html
        Parameters:	job_path - Name of Jenkins job, str
        Returns:    list of scm urls parsed from the job's config.xml
        '''
        scm_url_list = []
        if job_config := self.get_job_config_xml(job_path):
            root = ET.fromstring(job_config.text)

            for child in root.iter('scm'):
                for scm in child.iter('url'):
                    scm_url_list.append(scm.text)

            if not scm_url_list:
                scm_url_list.append("no_scm")
        else:
            self.log.error(f"Unable to find jobs for {job_path}")

        return scm_url_list

    def safe_response(self, resp):
        if resp.status_code != 200:
            return None
        return resp

    def strip_url(self, url):
        """
            Strips out jenkins host URL to return the Jenkins Job

            Example: https://jenkins.example.com/job/test-job would return job/test-job

            Parameters:	url - url of Jenkins job
            Returns:    (str) containing jenkins job
        """
        m = search(r'http(s|):\/\/.+(\.|:)(\d+|\w+)(\/|)(jenkins|)\/(.+)', url)
        return m.groups()[-1]
