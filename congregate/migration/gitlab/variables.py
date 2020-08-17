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

    def are_enabled(self, id):
        project = self.projects_api.get_project(
            id, self.config.source_host, self.config.source_token).json()
        return project.get("jobs_enabled", False)

    def get_gitlab_variables(self, id, host, token, var_type="projects"):
        if var_type == "group":
            return self.groups_api.get_all_group_variables(id, host, token)
        else:
            return self.projects_api.get_all_project_variables(id, host, token)

    def set_variables(self, id, data, host, token, var_type="projects"):
        if var_type == "group":
            return self.groups_api.create_group_variable(id, host, token, data)
        else:
            return self.projects_api.create_project_variable(id, host, token, data)

    def migrate_gitlab_cicd_variables(self, old_id, new_id, name, var_type):
        try:
            if self.are_enabled(old_id):
                var_list = safe_json_response(self.get_gitlab_variables(
                    old_id, self.config.source_host, self.config.source_token, var_type))
                if var_list:
                    return self.migrate_variables(new_id, var_list, var_type, name)
                else:
                    self.log.warning(
                        "Unable to retrieve variables from {}. Skipping variable migration".format(name))
                    return False
            else:
                self.log.warning(
                    "CI/CD is disabled for project {}".format(name))
        except Exception as e:
            self.log.error(
                "Failed to migrate project {0} CI/CD variables, with error:\n{1}".format(name, e))
            return False

    def migrate_variables(self, new_id, var_list, var_type, name):
        try:
            variables = iter(var_list)
            self.log.info(
                "Migrating {0} {1} CI/CD variables".format(var_type, name))
            for var in variables:
                if is_error_message_present(var) or not var:
                    self.log.error(
                        "Failed to fetch CI/CD variables ({0}) for project {1}".format(var, name))
                    return False
                self.log.info("Migrating {0} ID ({2}) CI/CD variables"
                              .format(var_type, new_id))
                self.set_variables(
                    new_id, var, self.config.destination_host, self.config.destination_token, var_type)
            return True
        except TypeError as te:
            self.log.error("{0} {1} variables {2}".format(
                var_type, name, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate project {0} CI/CD variables, with error:\n{1}".format(name, re))
            return False

    def migrate_variables_in_stage(self, dry_run=True):
        with open("%s/data/staged_projects.json" % self.app_path, "r") as f:
            files = json.load(f)
        ids = []
        project_id = None
        if len(files) > 0:
            for project_json in files:
                try:
                    self.log.info("Searching for existing project {}".format(
                        project_json["name"]))
                    for proj in self.projects_api.search_for_project(
                            self.config.destination_host,
                            self.config.destination_token,
                            project_json["name"]):
                        if proj["name"] == project_json["name"]:
                            if "%s" % project_json["namespace"].lower() in proj["path_with_namespace"].lower():
                                self.log.info("{0}Migrating variables for {1}"
                                              .format(get_dry_log(dry_run), proj["name"]))
                                project_id = proj["id"]
                                ids.append(project_id)
                                break
                            else:
                                project_id = None
                    if project_id is not None and not dry_run:
                        self.migrate_variables(
                            project_id, project_json["id"], "project", project_json["path_with_namespace"])
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
