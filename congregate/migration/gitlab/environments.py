from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.helpers.misc_utils import json_pretty


class EnvironmentsClient(BaseClass):
    def __init__(self):
        self.projects = ProjectsApi()
        super(EnvironmentsClient, self).__init__()

    def migrate_project_environments(self, src_id, dest_id, name):
        try:
            for environment in self.projects.get_all_environments(src_id, self.config.source_host, self.config.source_token):
                if "message" not in json_pretty(environment):
                    self.log.info("Migrating project {0} (ID: {1}) environment:\n{2}".format(
                        name, src_id, json_pretty(environment)))
                    self.projects.create_environment(
                        self.config.destination_host, self.config.destination_token, dest_id, self.generate_environment_data(environment))
        except RequestException as re:
            self.log.error(
                "Failed to migrate project {0} (ID: {1}) environments, with error:\n{2}".format(name, src_id, re))
            return False
        else:
            return True

    def generate_environment_data(self, environment):
        environment.pop("state")
        environment.pop("slug")
        environment.pop("id")
        return environment
