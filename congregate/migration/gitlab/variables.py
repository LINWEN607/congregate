import json

from requests.exceptions import RequestException
from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.migration.gitlab.api.projects import ProjectsApi


class VariablesClient(BaseClass):
    def __init__(self):
        self.projects = ProjectsApi()
        super(VariablesClient, self).__init__()

    def are_enabled(self, id):
        project = api.generate_get_request(self.config.source_host, self.config.source_token, "projects/%d" % id).json()
        return project.get("jobs_enabled", False)

    def get_variables(self, id, var_type="projects", instance_type="source"):
        if var_type == "group":
            endpoint = "groups/%d/variables" % id
        else:
            endpoint = "projects/%d/variables" % id

        if instance_type == "destination":
            host = self.config.destination_host
            token = self.config.destination_token
        else:
            host = self.config.source_host
            token = self.config.source_token

        return api.generate_get_request(host, token, endpoint)

    def set_variables(self, id, data, var_type="projects", instance_type="destination"):
        if var_type == "group":
            endpoint = "groups/%d/variables" % id
        else:
            endpoint = "projects/%d/variables" % id

        if instance_type == "source":
            host = self.config.source_host
            token = self.config.source_token
        else:
            host = self.config.destination_host
            token = self.config.destination_token

        return api.generate_post_request(host, token, endpoint, json.dumps(data))

    def migrate_cicd_variables(self, old_id, new_id, name):
        try:
            if self.are_enabled(old_id):
                self.log.info("Migrating {} CI/CD variables".format(name))
                self.migrate_variables(
                    new_id,
                    old_id,
                    "project")
                return True
            else:
                self.log.warning("CI/CD is disabled for project {}".format(name))
                return False
        except Exception, e:
            self.log.error("Failed to migrate {0} CI/CD variables, with error:\n{1}".format(name, e))
            return False

    def migrate_variables(self, new_id, old_id, var_type, dry_run=True):
        try:
            response = self.get_variables(old_id, var_type)
            if response.status_code == 200:
                variables = response.json()
                if len(variables) > 0:
                    for var in variables:
                        if var_type == "project":
                            var["environment_scope"] = "*"
                        self.log.info("{0}Migrating {1} variables".format(
                            "DRY-RUN: " if dry_run else "",
                            var_type))
                        if not dry_run:
                            self.set_variables(new_id, var, var_type)
                else:
                    self.log.info("Project does not have CI variables. Skipping.")
            else:
                self.log.error("Response returned a {0} with the message: {1}".format(
                    response.status_code,
                    response.text))
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
                    self.log.debug("Searching for existing %s" %
                                   project_json["name"])
                    for proj in self.projects.search_for_project(
                            self.config.destination_host,
                            self.config.destination_token,
                            project_json['name']):
                        if proj["name"] == project_json["name"]:
                            if "%s" % project_json["namespace"].lower() in proj["path_with_namespace"].lower():
                                self.log.debug("Migrating variables for %s" % proj["name"])
                                project_id = proj["id"]
                                ids.append(project_id)
                                break
                            else:
                                project_id = None
                    if project_id is not None:
                        self.migrate_variables(project_id, project_json["id"], "project")
                except IOError, e:
                    self.log.error(e)
            with open("%s/data/ids_variable.txt" % self.app_path, "w") as f:
                for i in ids:
                    f.write("%s\n" % i)
            return len(ids)
