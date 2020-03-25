from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present
from congregate.migration.gitlab.api.projects import ProjectsApi


class EnvironmentsClient(BaseClass):
    def __init__(self):
        self.projects = ProjectsApi()
        super(EnvironmentsClient, self).__init__()

    def migrate_project_environments(self, src_id, dest_id, name):
        try:
            resp = self.projects.get_all_environments(
                src_id, self.config.source_host, self.config.source_token)
            envs = iter(resp)
            self.log.info("Migrating project {} environments".format(name))
            for env in envs:
                if is_error_message_present(env):
                    self.log.warning(
                        "Failed to fetch environments ({0}) for project {1}".format(env, name))
                    return False
                self.projects.create_environment(
                    self.config.destination_host, self.config.destination_token, dest_id, self.generate_environment_data(env))
            return True
        except TypeError as te:
            self.log.error(
                "Project {0} environments {1} {2}".format(name, resp, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate project {0} environments, with error:\n{1}".format(name, re))
            return False

    def generate_environment_data(self, environment):
        environment.pop("state")
        environment.pop("slug")
        environment.pop("id")
        return environment
