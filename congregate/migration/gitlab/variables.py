import json

from requests.exceptions import RequestException
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import get_dry_log, is_error_message_present, safe_json_response
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi


class VariablesClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.groups_api = GroupsApi()
        super(VariablesClient, self).__init__()

    def get_ci_variables(self, id, host, token, var_type="projects"):
        if var_type == "group":
            return list(self.groups_api.get_all_group_variables(id, host, token))
        else:
            return list(self.projects_api.get_all_project_variables(id, host, token))

    def set_variables(self, id, data, host, token, var_type="projects"):
        if var_type == "group":
            return self.groups_api.create_group_variable(id, host, token, data)
        else:
            return self.projects_api.create_project_variable(id, host, token, data)

    def safe_add_variables(self, pid, param):
        result = False
        if param.get("value", None):
            new_var = self.set_variables(
                pid, param, self.config.destination_host, self.config.destination_token)
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
                    old_id, self.config.source_host, self.config.source_token, var_type=var_type)
                if var_list:
                    return self.migrate_variables(new_id, name, var_list, var_type)
                return True
            else:
                self.log.info(
                    f"CI/CD variables are disabled ({enabled}) for {var_type} {name}")
                return None
        except Exception as e:
            self.log.error(
                f"Failed to migrate {var_type} {name} CI/CD variables, with error:\n{e}")
            return False

    def migrate_pipeline_schedule_variables(self, old_id, new_id, name, enabled):
        try:
            if enabled:
                src_schedules = list(self.projects_api.get_all_project_pipeline_schedules(
                    old_id, self.config.source_host, self.config.source_token))
                if src_schedules:
                    dst_schedules = list(self.projects_api.get_all_project_pipeline_schedules(
                        new_id, self.config.destination_host, self.config.destination_token))
                    for sps in src_schedules:
                        for dps in dst_schedules:
                            if sps["description"] == dps["description"] and sps["ref"] == dps["ref"] and sps["cron"] == dps["cron"]:
                                self.log.info("Migrating project {} pipeline schedule ({}) variables".format(
                                    name, sps["description"]))
                                for v in safe_json_response(self.projects_api.get_single_project_pipeline_schedule(old_id, sps["id"], self.config.source_host, self.config.source_token)).get("variables", None):
                                    self.projects_api.create_new_project_pipeline_schedule_variable(
                                        new_id, dps["id"], self.config.destination_host, self.config.destination_token, v)
                return True
            else:
                self.log.info(
                    f"Pipeline schedule variables are disabled ({enabled}) for project {name}")
                return None
        except Exception as e:
            self.log.error(
                f"Failed to migrate project {name} pipeline schedule variables, with error:\n{e}")
            return False

    def migrate_variables(self, new_id, name, var_list, var_type):
        try:
            variables = iter(var_list)
            for var in variables:
                if is_error_message_present(var) or not var:
                    self.log.error(
                        f"Failed to fetch CI/CD variables ({var}) for {var_type} {name}")
                    return False
                self.log.info(
                    f"Migrating {var_type} {name} (ID: {new_id}) CI/CD variables")
                self.set_variables(
                    new_id, var, self.config.destination_host, self.config.destination_token, var_type=var_type)
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
        with open("%s/data/staged_projects.json" % self.app_path, "r") as f:
            files = json.load(f)
        ids = []
        project_id = None
        if len(files) > 0:
            for project_json in files:
                try:
                    old_id = project_json["id"]
                    project_name = proj["path_with_namespace"]
                    self.log.info("Searching for existing project {}".format(
                        project_json["name"]))
                    for proj in self.projects_api.search_for_project(
                            self.config.destination_host,
                            self.config.destination_token,
                            project_json["name"]):
                        if proj["name"] == project_json["name"]:
                            if "%s" % project_json["namespace"].lower() in project_name.lower():
                                self.log.info("{0}Migrating variables for {1}"
                                              .format(get_dry_log(dry_run), proj["name"]))
                                project_id = proj["id"]
                                ids.append(project_id)
                                break
                            else:
                                project_id = None
                    if project_id is not None and not dry_run:
                        self.migrate_cicd_variables(
                            old_id, project_id, project_name, "project")
                except IOError as e:
                    self.log.error(
                        "Failed to migrate variables in stage, with error:\n{}".format(e))
            self.log.info("{0}Writing {1} IDs to data/ids_variable.txt:\n{2}"
                          .format(get_dry_log(dry_run), len(ids), ids))
            if not dry_run:
                with open("%s/data/ids_variable.txt" % self.app_path, "w") as f:
                    for i in ids:
                        f.write("%s\n" % i)
            return len(ids)
