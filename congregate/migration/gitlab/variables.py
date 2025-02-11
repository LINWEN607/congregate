from requests.exceptions import RequestException
from requests import Response
from gitlab_ps_utils.misc_utils import is_error_message_present

from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from congregate.helpers.db_or_http import DbOrHttpMixin
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi


class VariablesClient(DbOrHttpMixin, BaseGitLabClient):
    def __init__(self, src_host=None, src_token=None, dest_host=None, dest_token=None):
        self.projects_api = ProjectsApi()
        self.groups_api = GroupsApi()
        super().__init__(src_host=src_host, src_token=src_token,
                         dest_host=dest_host, dest_token=dest_token)

    def get_ci_variables(self, id, host, token, var_type="projects", airgap=False):
        if var_type == "group":
            return list(
                self.groups_api.get_all_group_variables(id, host, token))
        return list(self.get_data(
            self.projects_api.get_all_project_variables,
            (id, host, token),
            'ci_variables',
            id,
            airgap=self.config.airgap,
            airgap_import=self.config.airgap_import)
        )

    def set_variables(self, oid, host, token, var_type="projects", data={}):
        if var_type == "group":
            return self.groups_api.create_group_variable(oid, host, token, data)
        return self.projects_api.create_project_variable(
            oid, host, token, data)

    def safe_add_variables(self, pid, param):
        result = False
        if param.get("value"):
            new_var = self.set_variables(
                pid, self.config.destination_host, self.config.destination_token, data=param)
            if new_var.status_code != 201:
                self.log.error(f"Unable to add variable {param['key']}")
            else:
                result = True
        else:
            self.log.warning(
                f"Skipping variable {param.get('key')} due to no value found")
        return result

    def migrate_cicd_variables(self, old_id, new_id, name, var_type, enabled):
        try:
            if enabled:
                var_list = self.get_ci_variables(
                    old_id, self.src_host, self.src_token, var_type=var_type)
                if var_list:
                    return self.migrate_variables(
                        new_id, name, var_list, var_type, old_id)
                return True
            self.log.info(
                f"Jobs i.e. CI/CD variables are disabled for {var_type} '{name}'")
            return None
        except Exception as e:
            self.log.error(
                f"Failed to migrate {var_type} {name} CI/CD variables, with error:\n{e}")
            return False

    def migrate_pipeline_schedule_variables(
            self, old_id, new_id, name, enabled):
        try:
            if enabled:
                src_schedules = list(self.get_data(
                    self.projects_api.get_all_project_pipeline_schedules,
                    (old_id, self.src_host, self.src_token),
                    'pipeline_schedules',
                    old_id,
                    airgap=self.config.airgap,
                    airgap_import=self.config.airgap_import))
                for sps in src_schedules:
                    if not self.config.airgap_export:
                        for dps in list(self.projects_api.get_all_project_pipeline_schedules(
                                new_id, self.dest_host, self.dest_token)):
                            if sps["description"] == dps["description"] and sps["ref"] == dps["ref"] and sps["cron"] == dps["cron"]:
                                self.handle_project_pipeline_variables(
                                    name, sps, dps['id'], new_id, old_id)
                    else:
                        self.send_data(
                            None,
                            None,
                            'pipeline_schedules',
                            old_id,
                            sps,
                            airgap=self.config.airgap,
                            airgap_export=self.config.airgap_export
                        )
                        self.handle_project_pipeline_variables(
                            name, sps, None, new_id, old_id)
                return True
            self.log.info(
                f"Project '{name}' pipeline schedule variables are disabled ({enabled})")
            return None
        except Exception as e:
            self.log.error(
                f"Failed to migrate project '{name}' pipeline schedule variables:\n{e}")
            return False

    def handle_project_pipeline_variables(self, p_name, sps, dps_id, new_id, old_id):
        self.log.info(
            f"Migrating project '{p_name}' pipeline schedule ({sps['description']}) variables")

        pipeline_schedule_vars = self.get_data(
            self.projects_api.get_single_project_pipeline_schedule,
            (old_id, sps["id"], self.src_host, self.src_token),
            'pipeline_schedule_variables',
            old_id,
            airgap=self.config.airgap,
            airgap_import=self.config.airgap_import
        )

        if isinstance(pipeline_schedule_vars, Response):
            pipeline_schedule_vars = pipeline_schedule_vars.json()['variables']

        for v in pipeline_schedule_vars:
            self.send_data(self.create_project_pipeline_schedule_variable,
                           (new_id, sps['id'], dps_id, self.dest_host,
                            self.dest_token, v),
                           f"pipeline_schedule_variables",
                           old_id,
                           {'schedule_id': sps['id'], **v},
                           airgap=self.config.airgap, airgap_export=self.config.airgap_export)

    def create_project_pipeline_schedule_variable(self, pid, spsid, dpsid, host, token, variable, data):
        if variable.get('schedule_id', -1) == spsid or not variable.get('schedule_id'):
            self.projects_api.create_new_project_pipeline_schedule_variable(
                pid, dpsid, host, token, data)

    def migrate_variables(self, new_id, name, var_list, var_type, src_id):
        try:
            for var in iter(var_list):
                error, var = is_error_message_present(var)
                if error or not var:
                    self.log.error(
                        f"Failed to fetch CI/CD variables ({var}) for {var_type} {name}")
                    return False
                self.log.info(
                    f"Migrating {var_type} {name} (ID: {new_id}) CI/CD variables")
                self.send_data(self.set_variables,
                               (new_id, self.dest_host, self.dest_token, var_type),
                               'ci_variables',
                               src_id,
                               var,
                               airgap=self.config.airgap,
                               airgap_export=self.config.airgap_export)
            return True
        except TypeError as te:
            self.log.error("{0} {1} variables {2}".format(
                var_type, name, te))
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate {var_type} {name} CI/CD variables, with error:\n{re}")
            return False
