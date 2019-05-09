from congregate.helpers.base_class import base_class
from congregate.helpers import api
from requests.exceptions import RequestException
import json

class gl_variables_client(base_class):
    def get_variables(self, id, var_type="projects", source_type="child"):
        if var_type == "group":
            endpoint = "groups/%d/variables" % id
        else:
            endpoint = "projects/%d/variables" % id

        if source_type == "parent":
            host = self.config.parent_host
            token = self.config.parent_token
        else:
            host = self.config.child_host
            token = self.config.child_token

        return api.generate_get_request(host, token, endpoint)

    def set_variables(self, id, data, var_type="projects", source_type="parent"):
        if var_type == "group":
            endpoint = "groups/%d/variables" % id
        else:
            endpoint = "projects/%d/variables" % id

        if source_type == "child":
            host = self.config.child_host
            token = self.config.child_token
        else:
            host = self.config.parent_host
            token = self.config.parent_token

        return api.generate_post_request(host, token, endpoint, json.dumps(data))

    def migrate_variables(self, new_id, old_id, var_type):
        try:
            response = self.get_variables(old_id, var_type)
            if response.status_code == 200:
                variables = response.json()
                if len(variables) > 0:
                    for var in variables:
                        if var_type == "project":
                            var["environment_scope"] = "*"
                        wrapped_data = json.dumps(var)
                        self.set_variables(new_id, wrapped_data, var_type)
                else:
                    self.l.logger.info("Project does not have CI variables. Skipping.")
            else:
                self.l.logger.error("Response returned a %d with the message: %s" % (response.status_code, response.text))
        except RequestException:
            return None

    def migrate_variables_in_stage(self):
        with open("%s/data/stage.json" % self.app_path, "r") as f:
            files = json.load(f)
        ids = []
        project_id = None
        if len(files) > 0:
            for project_json in files:
                try:
                    self.l.logger.debug("Searching for existing %s" % project_json["name"])
                    search_response = api.generate_get_request(self.config.parent_host, self.config.parent_token, 'projects', params={'search': project_json['name']}).json()
                    if len(search_response) > 0:
                        for proj in search_response:
                            if proj["name"] == project_json["name"]:
                                if "%s" % project_json["namespace"].lower() in proj["path_with_namespace"].lower():
                                    self.l.logger.debug("Migrating variables for %s" % proj["name"])
                                    project_id = proj["id"]
                                    ids.append(project_id)
                                    break
                                else:
                                    project_id = None
                    if project_id is not None:
                        self.migrate_variables(project_id, project_json["id"], "project")
                except IOError, e:
                    self.l.logger.error(e)
            with open("%s/data/ids_variable.txt" % self.app_path, "w") as f:
                for i in ids:
                    f.write("%s\n" % i)
            return len(ids)