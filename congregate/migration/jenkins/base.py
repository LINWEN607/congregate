import json
from congregate.helpers.base_class import BaseClass
from congregate.migration.jenkins.api.base import JenkinsApi


class JenkinsClient(BaseClass):
    def __init__(self):
        super(JenkinsClient, self).__init__()
        self.jenkins_api = JenkinsApi(self.config.ci_source_host, self.config.ci_source_username, self.config.ci_source_token)

    def retrieve_jobs_with_scm_info(self):
        """
        List and assigns jobs to associated SCM
        """
        data = self.jenkins_api.list_all_jobs()

        jobs_dict = {'jobs': []}
        for job in data['jobs']:
            job_name = job['fullname']
            scm_url = self.jenkins_api.get_scm_by_job(job_name)
            job_dict = {'name': job_name, 'url': scm_url}
            jobs_dict['jobs'].append(job_dict)
        with open('%s/data/jobs.json' % self.app_path, "w") as f:
            json.dump(jobs_dict, f, indent=4)

        return jobs_dict

    def transform_ci_variables(self, parameter):
        """
        Takes Jenkins param and returns it in expected format for GitLab. Will only work for standard
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
        if parameter["defaultParameterValue"] is not None:
            if "name" in parameter["defaultParameterValue"]:
                result_dict["key"] = parameter["defaultParameterValue"]["name"]
            if "value" in parameter["defaultParameterValue"]:
                result_dict["value"] = str(parameter["defaultParameterValue"]["value"])
        else:
            result_dict["key"] = parameter["name"]
            result_dict["value"] = "No Default Value"

        return result_dict
