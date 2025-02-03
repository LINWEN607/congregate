from requests.exceptions import RequestException
from dacite import from_dict

from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response

from congregate.helpers.db_or_http import DbOrHttpMixin
from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.meta.api_models.project_environment import NewProjectEnvironmentPayload
from congregate.migration.meta.api_models.project_protected_environment import NewProjectProtectedEnvironmentPayload


class EnvironmentsClient(DbOrHttpMixin, BaseGitLabClient):
    def __init__(self, src_host=None, src_token=None, dest_host=None, dest_token=None):
        self.projects = ProjectsApi()
        self.users = UsersApi()
        self.groups = GroupsApi()
        super().__init__(src_host=src_host, src_token=src_token, dest_host=dest_host, dest_token=dest_token)

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

            # Convert the response to a list, ensuring the generator is fully consumed
            envs = list(resp)

            if not envs:
                self.log.info(f"No environments found for project {name}")
                return True  # Return True, since there is nothing to migrate

            self.log.info(f"Migrating project {name} environments")
            for env in envs:
                # Check if env is actually a dictionary or object you can work with
                if not isinstance(env, dict):
                    self.log.error(f"Unexpected environment type for project {name}: {type(env)} - {env}")
                    continue  # Skip this environment since it's not a dicitionary
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

            # Migrate protected environments settings if there are any
            # Note: The import user should not be part of approvers or deployers because he is getting removed from the group later in the migration
            if not self.config.airgap:
                self.migrate_protected_environments_rules(src_id, dest_id)

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
        src_protected_envs = safe_json_response(self.projects.get_all_project_protected_environments(src_id, self.src_host, self.src_token))
        dest_protected_envs = safe_json_response(self.projects.get_all_project_protected_environments(dest_id, self.dest_host, self.dest_token))

        if not src_protected_envs:
            self.log.info(f"No protected environments found for project ID {src_id}")
            return

        # Update user and group IDs in source environments
        src_protected_envs = self.update_ids_in_protected_environments(src_protected_envs)

        # Filter out existing rules in the destination
        updated_envs = self.filter_existing_rules(src_protected_envs, dest_protected_envs)

        for env in updated_envs:
            if env['deploy_access_levels'] or env['approval_rules']:  # Only create/update if there are changes
                self.create_or_update_protected_environment(dest_id, env)

    def update_ids_in_protected_environments(self, protected_envs):
        for env in protected_envs:
            for access_level in env['deploy_access_levels']:
                if 'user_id' in access_level and access_level['user_id'] is not None:
                    self.log.debug(f"Fetching user details for user_id {access_level['user_id']}")
                    returned = self.users.get_user(access_level['user_id'], self.src_host, self.src_token).json()
                    email = returned.get("email")
                    if email:
                        self.log.debug(f"Found email {email} for user_id {access_level['user_id']}")
                        user_returned = safe_json_response(self.users.search_for_user_by_email(self.dest_host, self.dest_token, email))
                        if user_returned:
                            new_user_id = user_returned[0].get("id")
                            if new_user_id:
                                self.log.debug(f"Mapping user_id {access_level['user_id']} to new user_id {new_user_id}")
                                access_level['user_id'] = new_user_id
                            else:
                                self.log.warning(f"New user ID not found for email {email}")
                        else:
                            self.log.warning(f"Couldn't find destination user by email {email}")
                    else:
                        self.log.warning(f"Couldn't find email for user_id {access_level['user_id']}")

                if 'group_id' in access_level and access_level['group_id'] is not None:
                    self.log.debug(f"Fetching group details for group_id {access_level['group_id']}")
                    returned = self.groups.get_group(access_level['group_id'], self.src_host, self.src_token).json()
                    full_path = returned.get("full_path")
                    if full_path:
                        self.log.debug(f"Found full_path {full_path} for group_id {access_level['group_id']}")
                        group_returned = self.groups.get_group_by_full_path(full_path, self.dest_host, self.dest_token).json()
                        if group_returned:
                            new_group_id = group_returned.get("id")
                            if new_group_id:
                                self.log.debug(f"Mapping group_id {access_level['group_id']} to new group_id {new_group_id}")
                                access_level['group_id'] = new_group_id
                            else:
                                self.log.warning(f"New group ID not found for full_path {full_path}")
                        else:
                            self.log.warning(f"Couldn't find destination group by full_path {full_path}")
                    else:
                        self.log.warning(f"Couldn't find full_path for group_id {access_level['group_id']}")

            for rule in env['approval_rules']:
                if 'user_id' in rule and rule['user_id'] is not None:
                    self.log.debug(f"Fetching user details for user_id {rule['user_id']}")
                    returned = self.users.get_user(rule['user_id'], self.src_host, self.src_token).json()
                    email = returned.get("email")
                    if email:
                        self.log.debug(f"Found email {email} for user_id {rule['user_id']}")
                        user_returned = safe_json_response(self.users.search_for_user_by_email(self.dest_host, self.dest_token, email))
                        if user_returned:
                            new_user_id = user_returned[0].get("id")
                            if new_user_id:
                                self.log.debug(f"Mapping user_id {rule['user_id']} to new user_id {new_user_id}")
                                rule['user_id'] = new_user_id
                            else:
                                self.log.warning(f"New user ID not found for email {email}")
                        else:
                            self.log.warning(f"Couldn't find destination user by email {email}")
                    else:
                        self.log.warning(f"Couldn't find email for user_id {rule['user_id']}")

                if 'group_id' in rule and rule['group_id'] is not None:
                    self.log.debug(f"Fetching group details for group_id {rule['group_id']}")
                    returned = self.groups.get_group(rule['group_id'], self.src_host, self.src_token).json()
                    full_path = returned.get("full_path")
                    if full_path:
                        self.log.debug(f"Found full_path {full_path} for group_id {rule['group_id']}")
                        group_returned = self.groups.get_group_by_full_path(full_path, self.dest_host, self.dest_token).json()
                        if group_returned:
                            new_group_id = group_returned.get("id")
                            if new_group_id:
                                self.log.debug(f"Mapping group_id {rule['group_id']} to new group_id {new_group_id}")
                                rule['group_id'] = new_group_id
                            else:
                                self.log.warning(f"New group ID not found for full_path {full_path}")
                        else:
                            self.log.warning(f"Couldn't find destination group by full_path {full_path}")
                    else:
                        self.log.warning(f"Couldn't find full_path for group_id {rule['group_id']}")
        return protected_envs


    def create_or_update_protected_environment(self, pid, env):
        data = self.generate_protected_environment_data(environment=env)
        response = self.projects.create_protected_environment(self.dest_host, self.dest_token, pid, data)
        if response.status_code == 201:
            self.log.info(f"Protected environment '{env['name']}' created successfully")
        elif response.status_code == 409:
            data.pop("name", None)
            update_response = self.projects.update_protected_environment(self.dest_host, self.dest_token, pid, data, env['name'])
            if update_response.status_code == 200:
                self.log.info(f"Protected environment '{env['name']}' updated successfully")
            else:
                self.log.error(f"Failed to update protected environment '{env['name']}': {update_response.status_code} {update_response.text}")
        else:
            self.log.error(f"Failed to create protected environment '{env['name']}': {response.status_code} {response.text}")

    def filter_existing_rules(self, src_envs, dest_envs):
        for src_env in src_envs:
            for dest_env in dest_envs:
                if src_env['name'] == dest_env['name']:
                    src_env['deploy_access_levels'] = [
                        rule for rule in src_env['deploy_access_levels']
                        if not any(
                            rule['access_level'] == d_rule['access_level'] and
                            rule['user_id'] == d_rule['user_id'] and
                            rule['group_id'] == d_rule['group_id']
                            for d_rule in dest_env['deploy_access_levels']
                        )
                    ]
                    src_env['approval_rules'] = [
                        rule for rule in src_env['approval_rules']
                        if not any(
                            rule['access_level'] == d_rule['access_level'] and
                            rule['user_id'] == d_rule['user_id'] and
                            rule['group_id'] == d_rule['group_id']
                            for d_rule in dest_env['approval_rules']
                        )
                    ]
        return src_envs

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
