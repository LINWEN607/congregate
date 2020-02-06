from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.environments import EnvironmentsApi

class EnvironmentsClient(BaseClass):
    def __init__(self):
        self.environments = EnvironmentsApi()
        super(EnvironmentsClient, self).__init__()

    def migrate_project_environments(self, source_project_id, destination_project_id):
        for environment in self.environments.get_all_environments(source_project_id, self.config.source_host, self.config.source_token):
            self.environments.create_environment(self.config.destination_host, self.config.destination_token, destination_project_id, self.generate_environment_data(environment))

    def handle_project_environment_migration(self, destination_project_id, environment):
        self.environments.create_environment(self.config.destination_host, self.config.destination_token, destination_project_id, self.generate_environment_data(environment))

    def generate_environment_data(self, environment):
        environment.pop("state")
        environment.pop("slug")
        environment.pop("id")
        return environment