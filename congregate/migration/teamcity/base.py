from congregate.helpers.base_class import BaseClass
from congregate.migration.teamcity.api.base import TeamcityApi
from congregate.helpers.misc_utils import write_json_to_file, convert_to_underscores


class TeamcityClient(BaseClass):
    def __init__(self, host, user, token):
        super(TeamcityClient, self).__init__()
        self.teamcity_api = TeamcityApi(host, user, token)

    def retrieve_jobs_with_vcs_info(self, i):
        """
        List and assigns jobs to associated VCS
        """
        data = self.teamcity_api.list_build_configs()
        self.log.info("Listing endpoint: Teamcity Jobs")
        jobs_list = []
        for job in data['buildTypes']['buildType']:
            job_name = job['@id']
            scm_data = self.teamcity_api.get_build_vcs_roots(job_name)
            if scm_data != "no_scm":
                for property_node in scm_data["vcs-root"]["properties"]["property"]:
                    if property_node["@name"] == "url":
                        scm_url = property_node["@value"]
                job_dict = {'name': job_name, 'url': scm_url}
                jobs_list.append(job_dict)
            else:
                job_dict = {'name': job_name, 'url': "no_scm"}
                jobs_list.append(job_dict)

        write_json_to_file(f"{self.app_path}/data/teamcity_jobs_{i}.json", jobs_list)

        return data

    def transform_ci_variables(self, parameter):
        """
        Takes Teamcity param and returns it in expected format for GitLab. Will only work for standard
        {
            "key": "NEW_VARIABLE",
            "value": "new value",
            "protected": false,
            "variable_type": "env_var",
            "masked": false,
            "environment_scope": "*"
        }
        """
        result_dict = {}
        if isinstance(parameter, dict):
            result_dict = {
                "key": convert_to_underscores(parameter["@name"]), 
                "protected": False, 
                "variable_type": "env_var", 
                "masked": False, 
                "environment_scope": "teamcity"
            }
            if parameter.get("@value", None):
                result_dict["value"] = parameter["@value"]
            else:
                result_dict["value"] = "No Default Value"

        return result_dict
