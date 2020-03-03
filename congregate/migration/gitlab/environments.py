from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.projects import ProjectsApi


class EnvironmentsClient(BaseClass):
    def __init__(self):
        self.projects = ProjectsApi()
        super(EnvironmentsClient, self).__init__()

    def migrate_project_environments(self, source_project_id, destination_project_id):
        try:
            for environment in self.projects.get_all_environments(source_project_id, self.config.source_host, self.config.source_token):
                self.projects.create_environment(self.config.destination_host, self.config.destination_token,
                                                 destination_project_id, self.generate_environment_data(environment))
        except Exception as e:
            self.log.error(
                "Failed to migrate project (ID: {0}) environments, with error:\n{1}".format(source_project_id, e))
            return False
        else:
            return True

    def generate_environment_data(self, environment):
        environment.pop("state")
        environment.pop("slug")
        environment.pop("id")
        return environment
