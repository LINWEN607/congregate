from http.server import executable
from requests.exceptions import RequestException
from pathlib import Path
from congregate.helpers.base_class import BaseClass
from gitlab_ps_utils.misc_utils import is_error_message_present
from gitlab_ps_utils.dict_utils import pop_multiple_keys
from congregate.migration.gitlab.api.packages import PackagesApi


class PackagesClient(BaseClass):
    def __init__(self):
        self.packages = PackagesApi()
        super(PackagesClient, self).__init__()

    def migrate_project_packages(self, src_id, dest_id):
        self.log.info(f"Migrating project {src_id} packages")
        for package in self.packages.get_project_packages(self.config.source_host, self.config.source_token, src_id):
            if self.get_package_type(package) == 'maven':
                executable = None
                pom_file = None
                for package_file in self.packages.get_package_files(self.config.source_host, self.config.source_token, src_id, package.get('id')):
                    if Path(package_file.get('file_name')).suffix == '.pom':
                        pom_file = package_file['file_name']
                    if Path(package_file.get('file_name')).suffix in ['.jar', '.war', '.ear']:
                        executable = package_file['file_name']
                if executable and pom_file:
                    pass

            else:
                self.log.info(f"{package.get('name')} is not a maven package and thus not supported at this time, skipping")


    def get_package_type(self, package):
        return package.get("package_type")

    def migrate_project_environments(self, src_id, dest_id, name, enabled):
        try:
            if not enabled:
                self.log.info(
                    f"Environments are disabled ({enabled}) for project {name}")
                return None
            resp = self.projects.get_all_project_environments(
                src_id, self.config.source_host, self.config.source_token)
            envs = iter(resp)
            self.log.info("Migrating project {} environments".format(name))
            for env in envs:
                error, env = is_error_message_present(env)
                if error or not env:
                    self.log.error(
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
        return pop_multiple_keys(environment, ["state", "slug", "id"])