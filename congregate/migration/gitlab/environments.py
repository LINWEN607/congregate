from requests.exceptions import RequestException
from dacite import from_dict

from congregate.helpers.db_or_http import DbOrHttpMixin
from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from gitlab_ps_utils.misc_utils import is_error_message_present
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.meta.api_models.project_environment import NewProjectEnvironmentPayload


class EnvironmentsClient(DbOrHttpMixin, BaseGitLabClient):
    def __init__(self, src_host=None, src_token=None, dest_host=None, dest_token=None):
        self.projects = ProjectsApi()
        super(EnvironmentsClient, self).__init__(src_host=src_host, src_token=src_token, dest_host=dest_host, dest_token=dest_token)

    def migrate_project_environments(self, src_id, dest_id, name, enabled):
        try:
            if not enabled:
                self.log.info(
                    f"Environments are disabled ({enabled}) for project {name}")
                return None
            resp = self.get_data(
                self.projects.get_all_project_environments,
                (src_id, self.src_host, self.src_token),
                'project_environments', 
                src_id,
                airgap=self.config.airgap,
                airgap_import=self.config.airgap_import)
            envs = iter(resp)
            self.log.info(f"Migrating project {name} environments")
            for env in envs:
                error, env = is_error_message_present(env)
                if error or not env:
                    self.log.error(
                        f"Failed to fetch environments ({env}) for project {name}")
                    return False
                self.send_data(
                    self.projects.create_environment,
                    (self.dest_host, self.dest_token, dest_id),
                    'project_environments',
                    src_id,
                    self.generate_environment_data(env), 
                    airgap=self.config.airgap,
                    airgap_export=self.config.airgap_export)
            return True
        except TypeError as te:
            self.log.error(
                f"Project {name} environments {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate project {name} environments, with error:\n{re}")
            return False

    def generate_environment_data(self, environment):
        return from_dict(data_class=NewProjectEnvironmentPayload, data=environment).to_dict()
