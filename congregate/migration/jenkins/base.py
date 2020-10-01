from congregate.helpers.base_class import BaseClass
from congregate.migration.jenkins.api.base import JenkinsApi
from congregate.helpers.misc_utils import write_json_to_file, convert_to_underscores

class JenkinsClient(BaseClass):
    def __init__(self):
        super(JenkinsClient, self).__init__()
        self.jenkins_api = JenkinsApi(self.config.ci_source_host, self.config.ci_source_username, self.config.ci_source_token)

    def retrieve_jobs_with_scm_info(self):
        """
        List and assigns jobs to associated SCM
        """
        data = self.jenkins_api.list_all_jobs()

        jobs_list = []
        for job in data:
            job_path = self.jenkins_api.strip_url(job["url"]).rstrip('/')
            # job_path = (job["url"].replace(self.config.ci_source_host, "")).strip('/')
            scm_url_list = self.jenkins_api.get_scm(job_path)
            for scm_url in scm_url_list:
                job_dict = {'name': job_path, 'url': scm_url}
                jobs_list.append(job_dict)

        write_json_to_file(f"{self.app_path}/data/jenkins_jobs.json", jobs_list)

        return jobs_list

    def transform_ci_variables(self, parameter):
        """
        Takes Jenkins param and returns it in expected format for GitLab. Will only work for standard
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
        result_dict = {"protected": False, "variable_type": "env_var", "masked": False, "environment_scope": "jenkins"}

        result_dict["key"] = convert_to_underscores(parameter["name"])
        if parameter.get("defaultValue") is not None:
            result_dict["value"] = str(parameter["defaultValue"])
        else:
            result_dict["value"] = "No Default Value"

        return result_dict
