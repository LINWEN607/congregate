from requests.exceptions import RequestException
from dacite import from_dict
import traceback
import time

from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response

from congregate.helpers.db_or_http import DbOrHttpMixin
from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.meta.api_models.project_environment import NewProjectEnvironmentPayload
from congregate.migration.meta.api_models.project_protected_environment import NewProjectProtectedEnvironmentPayload


class EnvironmentsClient(DbOrHttpMixin, BaseGitLabClient):
    def __init__(self, src_host=None, src_token=None, dest_host=None, dest_token=None):
        self.projects = ProjectsApi()
        super(EnvironmentsClient, self).__init__(src_host=src_host,
                                                 src_token=src_token, dest_host=dest_host, dest_token=dest_token)

    def migrate_project_environments(self, src_id, dest_id, name, enabled):
        try:
            if not enabled:
                self.log.info(
                    f"Environments are disabled ({enabled}) for project {name}")
                return None

            # Migrate environments
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
                if create_resp := self.send_data(
                    self.projects.create_environment,
                    (self.dest_host, self.dest_token, dest_id),
                    'project_environments',
                    src_id,
                    self.generate_environment_data(env),
                    airgap=self.config.airgap,
                    airgap_export=self.config.airgap_export):
                    self.update_state(name, dest_id, env, create_resp)

            # Migrate protected environments settings
            # Note: The import user should not be part of approvers or deployers because he is getting removed from the group later in the migration
            if not self.migrate_protected_environments_rules(src_id, dest_id):
                self.log.error(f"Failed to migrate protected environments rules for project {name}")

            return True
        except TypeError as te:
            self.log.error(
                f"Project '{name}' environments {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate project '{name}' environments, with error:\n{re}")
            return False

    def migrate_protected_environments_rules(self, src_id, dest_id):
        try:
            src_protected_envs = safe_json_response(self.projects.get_all_project_protected_environments(src_id, self.src_host, self.src_token))

            for env in src_protected_envs:
                self.create_or_update_protected_environment(dest_id, env)

            return True
        except Exception as e:
            self.log.error(f"Exception during protected environment migration: {e}")
            print(traceback.format_exc())
            return False

    def create_or_update_protected_environment(self, pid, env):
        #First, try to unprotect the environment if it already exists
        if self.unprotect_environment(pid, env['name']):
            self.log.info(f"Protected environment '{env['name']}' unprotected successfully")
            data = self.generate_protected_environment_data(environment=env)
            response = self.projects.create_protected_environment(self.dest_host, self.dest_token, pid, data)
            if response.status_code == 201:
                self.log.info(f"Protected environment '{env['name']}' created successfully. Response = {response.text}")
            elif response.status_code == 409:
                # This is in case the environment could not be unprotected. Then we just update it.
                # Note: The api duplicates rules if they were already existing this is why it's not the prefered option
                data.pop("name", None)
                update_response = self.projects.update_protected_environment(self.dest_host, self.dest_token, pid, data, env['name'])
                if update_response.status_code != 200:
                    self.log.error(f"Failed to update protected environment '{env['name']}': {response.status_code} {response.text}")
            else:
                self.log.error(f"Failed to create protected environment '{env['name']}': {response.status_code} {response.text}")
    
    def unprotect_environment(self, pid, env_name):
        response = self.projects.unprotect_environment(self.dest_host, self.dest_token, pid, env_name)
        if response.status_code == 204:
            return True
        elif response.status_code == 404:
            self.log.info(f"Protected environment '{env_name}' does not exist, no need to unprotect")
            return True
        else:
            self.log.error(f"Failed to unprotect environment '{env_name}': {response.status_code} {response.text}")
            return False

    def generate_environment_data(self, environment):
        return from_dict(data_class=NewProjectEnvironmentPayload, data=environment).to_dict()
    
    def generate_protected_environment_data(self, environment):
        return from_dict(data_class=NewProjectProtectedEnvironmentPayload, data=environment).to_dict()

    def update_state(self, name, dest_id, env, resp):
        if resp.status_code != 201:
            self.log.error(
                f"Failed to create project '{name}' environment:\n{resp} - {resp.text}")
        elif env.get("state") in ["stopping", "stopped"]:
            resp_json = safe_json_response(resp) or {}
            env_id = resp_json.get("id")
            update_resp = self.projects.stop_environment(
                self.dest_host, self.dest_token, dest_id, env_id, {"force": True})
            if update_resp.status_code != 200:
                self.log.error(
                    f"Failed to stop project '{name}' environment '{env.get('name')}' (Env ID: {env_id})")
