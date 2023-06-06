from requests.exceptions import RequestException
from gitlab_ps_utils.misc_utils import get_dry_log, is_error_message_present, safe_json_response
from gitlab_ps_utils.json_utils import read_json_file_into_object

from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from congregate.helpers.db_or_http import DbOrHttpMixin
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi


class VariablesClient(DbOrHttpMixin, BaseGitLabClient):
    def __init__(self, src_host=None, src_token=None):
        self.projects_api = ProjectsApi()
        self.groups_api = GroupsApi()
        super(VariablesClient, self).__init__(
            src_host=src_host, src_token=src_token)

    def get_ci_variables(self, id, host, token, var_type="projects"):
        if var_type == "group":
            return list(
                self.groups_api.get_all_group_variables(id, host, token))
        else:
            return list(
                self.projects_api.get_all_project_variables(id, host, token))

    def set_variables(self, id, host, token, var_type="projects", data={}):
        if var_type == "group":
            return self.groups_api.create_group_variable(id, host, token, data)
        else:
            return self.projects_api.create_project_variable(
                id, host, token, data)

    def safe_add_variables(self, pid, param):
        result = False
        if param.get("value", None):
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
                src_schedules = list(self.projects_api.get_all_project_pipeline_schedules(
                    old_id, self.src_host, self.src_token))
                if src_schedules:
                    dst_schedules = list(self.projects_api.get_all_project_pipeline_schedules(
                        new_id, self.config.destination_host, self.config.destination_token))
                    for sps in src_schedules:
                        for dps in dst_schedules:
                            if sps["description"] == dps["description"] and sps["ref"] == dps["ref"] and sps["cron"] == dps["cron"]:
                                self.log.info("Migrating project {} pipeline schedule ({}) variables".format(
                                    name, sps["description"]))
                                for v in safe_json_response(self.projects_api.get_single_project_pipeline_schedule(
                                        old_id, sps["id"], self.src_host, self.src_token)).get("variables", None):

                                    self.send_data(self.projects_api.create_new_project_pipeline_schedule_variable,
                                                   (new_id, dps["id"], self.config.destination_host,
                                                    self.config.destination_token, v),
                                                   f"pipeline_schedule_variables.{dps['id']}.variables",
                                                   old_id,
                                                   v, airgap=self.config.airgap)
                return True
            self.log.info(
                f"Pipeline schedule variables are disabled ({enabled}) for project {name}")
            return None
        except Exception as e:
            self.log.error(
                f"Failed to migrate project {name} pipeline schedule variables, with error:\n{e}")
            return False

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
                               (new_id, self.config.destination_host,
                                self.config.destination_token, var_type),
                               'ci_variables',
                               src_id,
                               var, airgap=self.config.airgap)
            return True
        except TypeError as te:
            self.log.error("{0} {1} variables {2}".format(
                var_type, name, te))
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate {var_type} {name} CI/CD variables, with error:\n{re}")
            return False

    def migrate_variables_in_stage(self, dry_run=True):
        sps = read_json_file_into_object(
            f"{self.app_path}/data/staged_projects.json")
        ids = []
        for sp in sps:
            try:
                project_path = sp["path_with_namespace"]
                self.log.info(
                    f"Searching on destination for project '{project_path}'")
                resp = self.projects_api.get_project_by_path_with_namespace(
                    project_path, self.config.destination_host, self.config.destination_token)
                if resp.status_code != 200:
                    self.log.warning(
                        f"SKIP: Project '{project_path}' does not exist: {resp} - {resp.text})")
                    continue
                self.log.info(
                    f"{get_dry_log(dry_run)}Migrating project '{project_path}' variables")
                project = safe_json_response(resp)
                pid = project.get("id") if project else None
                ids.append(pid)
                if pid and not dry_run:
                    self.migrate_cicd_variables(
                        sp.get("id"), pid, project_path, "project", sp.get("jobs_enabled"))
                text_file = "data/project_ids_variables.txt"
                self.log.info(
                    f"{get_dry_log(dry_run)}Writing {len(ids)} project IDs to '{text_file}'")
                if not dry_run:
                    with open(f"{self.app_path}/{text_file}", "w") as f:
                        f.write('\n'.join(id for id in ids))
            except RequestException as re:
                self.log.error(
                    f"Failed to create project '{project_path}' variables:\n{re}")
            except IOError as ioe:
                self.log.error(
                    f"Failed to write project '{project_path}' ID to file:\n{ioe}")
            return len(ids)
