import re
from congregate.helpers.base_class import BaseClass
from congregate.migration.teamcity.api.base import TeamcityApi
from congregate.helpers.misc_utils import convert_to_underscores, strip_protocol, dig
from congregate.helpers.processes import start_multi_process_stream
from congregate.helpers.mdbc import MongoConnector


class TeamcityClient(BaseClass):
    def __init__(self, host, user, token):
        super().__init__()
        self.teamcity_api = TeamcityApi(host, user, token)

    def retrieve_jobs_with_vcs_info(self, i, processes=None):
        """
        List and assigns jobs to associated SCM
        """
        build_configs = self.teamcity_api.list_build_configs()
        start_multi_process_stream(self.handle_retrieving_tc_jobs, dig(
            build_configs, 'buildTypes', 'buildType'), processes=processes)

    def handle_retrieving_tc_jobs(self, job):
        mongo = MongoConnector()
        job_name = job['@id']
        scm_data = self.teamcity_api.get_build_vcs_roots(job_name)
        tc_host = strip_protocol(self.teamcity_api.host)
        if scm_data != "no_scm":
            for property_node in dig(scm_data, 'vcs-root', 'properties', 'property', default=[]):
                if property_node["@name"] == "url":
                    # Regex replaces URL where '#refs' is found and trims it.
                    scm_url = re.sub("([#]refs.*)", "",
                                     property_node["@value"])
            job_dict = {'name': job_name, 'url': scm_url}
            self.log.info(
                f"Inserting TC job {job_name} from {tc_host} into mongo")
            mongo.insert_data(f"teamcity-{tc_host}", job_dict)
        else:
            job_dict = {'name': job_name, 'url': "no_scm"}
            self.log.info(
                f"Inserting TC job {job_name} from {tc_host} with no SCM attached into mongo")
            mongo.insert_data(f"teamcity-{tc_host}", job_dict)
        mongo.close_connection()

    def transform_ci_variables(self, parameter, tc_ci_src_hostname):
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
        temp_url = strip_protocol(tc_ci_src_hostname).split(":")[0]
        result_dict = {}
        if isinstance(parameter, dict):
            result_dict = {
                "key": convert_to_underscores(parameter["@name"]),
                "protected": False,
                "variable_type": "env_var",
                "masked": False,
                "environment_scope": f"teamcity-{temp_url}"
            }
            if parameter.get("@value", None):
                result_dict["value"] = parameter["@value"]
            else:
                result_dict["value"] = "No Default Value"
        return result_dict
