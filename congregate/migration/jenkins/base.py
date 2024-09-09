from congregate.migration.meta.base_ext_ci import BaseExternalCiClient
from congregate.migration.jenkins.api.base import JenkinsApi
from gitlab_ps_utils.misc_utils import strip_netloc
from gitlab_ps_utils.string_utils import convert_to_underscores
from congregate.helpers.congregate_mdbc import CongregateMongoConnector


class JenkinsClient(BaseExternalCiClient):
    ci_source = "jenkins"

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
            mongo = CongregateMongoConnector()
        job_path = self.jenkins_api.strip_url(job["url"]).rstrip('/')
        scm_url_list = self.jenkins_api.get_scm(job_path)
        jenkins_host = strip_netloc(self.jenkins_api.host)
        for scm_url in scm_url_list:
            job_dict = {'name': job_path, 'url': scm_url}
            self.log.info(
                f"Inserting job {job_dict} from {jenkins_host} into mongo")
            mongo.insert_data(f"jenkins-{jenkins_host}", job_dict)
        mongo.close_connection()

    def transform_ci_variables(self, parameter, ci_src_hostname):
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
        temp_url = strip_netloc(ci_src_hostname).split(":")[0]
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

    def migrate_variables(
            self, project, new_id, ci_src_hostname):
        if (ci_sources := project.get("ci_sources", None)):
            result = True
            for job in ci_sources.get("Jenkins", []):
                params = self.jenkins_api.get_job_params(job)
                for param in params:
                    if not self.variables.safe_add_variables(
                        new_id,
                        self.transform_ci_variables(
                            param, ci_src_hostname)
                    ):
                        result = False
            return result
        return None

    def migrate_build_configuration(self, project, project_id):
        '''
        In order to maintain configuration from old Jenkins instance,
        we save a copy of a Jenkins job config.xml file and commit it to the associated repository.
        '''
        if (ci_sources := project.get("ci_sources", None)):
            is_result = False
            for job in ci_sources.get("Jenkins", []):
                if config_xml := self.jenkins_api.get_job_config_xml(
                        job):
                    # Create branch for config.xml
                    branch_data = {
                        "branch": f"{job.lstrip('/')}-jenkins-config",
                        "ref": "master"
                    }
                    self.projects_api.create_branch(
                        self.config.destination_host,
                        self.config.destination_token,
                        project_id,
                        data=branch_data
                    )
                    content = config_xml.text
                    data = {
                        "branch": f"{job.lstrip('/')}-jenkins-config",
                        "commit_message": "[skip ci] Adding 'config.xml' for Jenkins job",
                        "content": content
                    }

                    req = self.project_repository_api.create_repo_file(
                        self.config.destination_host, self.config.destination_token,
                        project_id, "config.xml", data)
                    is_result = bool(req.status_code == 200)
            return is_result
        return None
