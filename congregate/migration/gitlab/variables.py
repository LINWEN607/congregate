import json

from requests.exceptions import RequestException
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import get_dry_log
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

    def get_variables(self, id, host, token, var_type="projects"):
        if var_type == "group":
            return self.groups_api.get_all_group_variables(id, host, token)
        else:
            return self.projects_api.get_all_project_variables(id, host, token)

    def set_variables(self, id, data, host, token, var_type="projects", instance_type="destination"):
        if var_type == "group":
            return self.groups_api.create_group_variable(id, host, token, data)
        else:
            return self.projects_api.create_project_variable(id, host, token, data)

    def migrate_cicd_variables(self, old_id, new_id, name):
        try:
            if self.are_enabled(old_id):
                self.log.info(
                    "Migrating project {} CI/CD variables".format(name))
                self.migrate_variables(new_id, old_id, "project")
                return True
            else:
                self.log.warning(
                    "CI/CD is disabled for project {}".format(name))
                return False
        except Exception, e:
            self.log.error(
                "Failed to migrate project {0} CI/CD variables, with error:\n{1}".format(name, e))
            return False

    def migrate_variables(self, new_id, old_id, var_type):
        try:
            response = self.get_variables(
                old_id, self.config.source_host, self.config.source_token, var_type)
            if response.status_code == 200:
                variables = response.json()
                if len(variables) > 0:
                    for var in variables:
                        if var_type == "project":
                            var["environment_scope"] = "*"
                        self.log.info("Migrating {0} ID (old: {1}; new: {2}) variables"
                                      .format(var_type, old_id, new_id))
                        self.set_variables(
                            new_id, var, self.config.destination_host, self.config.destination_token, var_type)
                else:
                    self.log.info("SKIP: Project (old: {0}; new: {1}) does not have CI variables"
                                  .format(old_id, new_id))
            else:
                self.log.error(
                    "Failed to get variables, response: {}".format(response))
        except RequestException:
            return None

    def migrate_variables_in_stage(self, dry_run=True):
        with open("%s/data/stage.json" % self.app_path, "r") as f:
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
                            project_json['name']):
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
                            project_id, project_json["id"], "project")
                except IOError, e:
                    self.log.error(
                        "Failed to migrate variables in stage, with error:\n{}".format(e))
            self.log.info("{0}Writing {1} IDs to data/ids_variable.txt:\n{2}"
                          .format(get_dry_log(dry_run), len(ids), ids))
            if not dry_run:
                with open("%s/data/ids_variable.txt" % self.app_path, "w") as f:
                    for i in ids:
                        f.write("%s\n" % i)
            return len(ids)
