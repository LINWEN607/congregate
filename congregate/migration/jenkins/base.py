from congregate.helpers.base_class import BaseClass
from congregate.migration.jenkins.api.base import JenkinsApi
from congregate.helpers.misc_utils import strip_netloc
from congregate.helpers.string_utils import convert_to_underscores
from congregate.helpers.mdbc import MongoConnector


class JenkinsClient(BaseClass):
    def __init__(self, host, user, token):
        super().__init__()
        self.jenkins_api = JenkinsApi(host, user, token)

    def retrieve_jobs_with_scm_info(self, i, processes=None):
        """
        List and assigns jobs to associated SCM
        """
        self.multi.start_multi_process_stream(self.handle_retrieving_jenkins_jobs,
                                              self.jenkins_api.list_all_jobs(), processes=processes)

    def handle_retrieving_jenkins_jobs(self, job, mongo=None):
        if mongo is None:
            mongo = MongoConnector()
        job_path = self.jenkins_api.strip_url(job["url"]).rstrip('/')
        scm_url_list = self.jenkins_api.get_scm(job_path)
        jenkins_host = strip_netloc(self.jenkins_api.host)
        for scm_url in scm_url_list:
            job_dict = {'name': job_path, 'url': scm_url}
            self.log.info(
                f"Inserting job {job_dict} from {jenkins_host} into mongo")
            mongo.insert_data(f"jenkins-{jenkins_host}", job_dict)
        mongo.close_connection()

    def transform_ci_variables(self, parameter, jenkins_ci_src_hostname):
        """
        Takes a Jenkins Parameter and returns it in GitLab format.
        Will only work for standard parameters.

        Accepts parameter provided as:
        {
            "name": "Jenkins Parameter",
            "defaultValue": "value"
        }
        Returns:
        {
            "key": "NEW_VARIABLE",
            "value": "new value",
            "protected": false,
            "variable_type": "env_var",
            "masked": false,
            "environment_scope": "*"
        }
        """
        temp_url = strip_netloc(jenkins_ci_src_hostname).split(":")[0]
        result_dict = {
            "protected": False,
            "variable_type": "env_var",
            "masked": False,
            "environment_scope": f"jenkins-{temp_url}"
        }
        result_dict["key"] = convert_to_underscores(parameter["name"])
        if parameter.get("defaultValue") is not None:
            result_dict["value"] = str(parameter["defaultValue"])
        else:
            result_dict["value"] = "No Default Value"
        return result_dict
