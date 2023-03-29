"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2023 - GitLab
"""

import re
import xml.dom.minidom
from gitlab_ps_utils.misc_utils import strip_netloc
from gitlab_ps_utils.dict_utils import dig
from gitlab_ps_utils.string_utils import convert_to_underscores
from congregate.migration.meta.base_ext_ci import BaseExternalCiClient
from congregate.migration.teamcity.api.base import TeamcityApi
from congregate.helpers.mdbc import MongoConnector


class TeamcityClient(BaseExternalCiClient):
    def __init__(self, host, user, token):
        super().__init__()
        self.teamcity_api = TeamcityApi(host, user, token)

    def retrieve_jobs_with_scm_info(self, i, processes=None):
        """
        List and assigns jobs to associated SCM
        """
        build_configs = self.teamcity_api.list_build_configs()
        self.multi.start_multi_process_stream(self.handle_retrieving_tc_jobs, dig(
            build_configs, 'buildTypes', 'buildType'), processes=processes)

    def handle_retrieving_tc_jobs(self, job):
        mongo = MongoConnector()
        job_name = job['@id']
        scm_data = self.teamcity_api.get_build_vcs_roots(job_name)
        tc_host = strip_netloc(self.teamcity_api.host)
        if scm_data != "no_scm":
            for property_node in dig(
                    scm_data, 'vcs-root', 'properties', 'property', default=[]):
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

    def transform_ci_variables(self, parameter, ci_src_hostname):
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
        temp_url = strip_netloc(ci_src_hostname).split(":")[0]
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

    def migrate_variables(
            self, project, new_id, ci_src_hostname):
        if (ci_sources := project.get("ci_sources", None)):
            result = True
            for job in ci_sources.get("TeamCity", []):
                params = self.teamcity_api.get_build_params(job)
                try:
                    if params.get("properties", None) is not None:
                        for param in dig(
                                params, "properties", "property", default=[]):
                            if not self.variables.safe_add_variables(
                                new_id,
                                self.transform_ci_variables(
                                    param, ci_src_hostname)
                            ):
                                result = False
                    else:
                        self.log.warning(
                            f"Job: {job} had no param properties present")
                except AttributeError as e:
                    self.log.error(
                        f"Attribute Error Caught for Job:{job} Params:{params} with error:{e}")
            return result
        return None

    def migrate_build_configuration(self, project, project_id):
        '''
        In order to maintain configuration from old TeamCity instance,
        we save a copy of a TeamCity's job build configuration file and commit it to the associated repository.
        '''
        is_result = True
        if ci_sources := project.get("ci_sources", None):
            for job in ci_sources.get("TeamCity", []):
                if build_config := self.teamcity_api.get_build_config(
                        job):
                    # Create branch for TeamCity configuration
                    branch_data = {
                        "branch": f"{job}-teamcity-config",
                        "ref": "master"
                    }
                    self.projects_api.create_branch(
                        self.config.destination_host,
                        self.config.destination_token,
                        project_id,
                        data=branch_data
                    )

                    dom = xml.dom.minidom.parseString(build_config.text)
                    build_config = dom.toprettyxml()

                    data = {
                        "branch": f"{job}-teamcity-config",
                        "commit_message": "Adding build_config.xml for TeamCity job",
                        "content": build_config
                    }

                    req = self.project_repository_api.create_repo_file(
                        self.config.destination_host, self.config.destination_token,
                        project_id, "build_config.xml", data)

                    if req.status_code != 200:
                        is_result = False

                    for url in self.teamcity_api.get_maven_settings_file_links(
                            job):
                        file_name, content = self.teamcity_api.extract_maven_xml(
                            url)
                        if content:
                            data = {
                                "branch": f"{job}-teamcity-config",
                                "commit_message": f"Adding {file_name} for TeamCity job",
                                "content": content
                            }
                            req = self.project_repository_api.create_repo_file(
                                self.config.destination_host, self.config.destination_token,
                                project_id, file_name, data)

                            if req.status_code != 200:
                                is_result = False

        return is_result