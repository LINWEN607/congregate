from base64 import b64encode
import sys
import requests

from gitlab_ps_utils.exceptions import ConfigurationException
from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response
from gitlab_ps_utils.json_utils import json_pretty
from congregate.helpers.conf import Config
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.helpers.utils import is_github_dot_com, is_dot_com


class ConfigurationValidator(Config):
    '''
    Extended config class used to validate the configuration on run
    '''

    GET_TIMEOUT = 10

    def __init__(self, path=None):
        self.groups = GroupsApi()
        self.users = UsersApi()
        self._dstn_parent_id_validated_in_session = False
        self._import_user_id_validated_in_session = False
        self._dstn_parent_group_path_validated_in_session = False
        self._dstn_token_validated_in_session = False
        self._src_token_validated_in_session = False
        self._airgap_validated_in_session = False
        self._direct_transfer_validated_in_session = False
        super().__init__(path=path)

    @property
    def dstn_parent_id(self):
        dstn_parent_id = self.prop_int("DESTINATION", "dstn_parent_group_id")
        if self.dstn_parent_id_validated_in_session:
            return dstn_parent_id
        self.dstn_parent_id_validated_in_session = self.validate_dstn_parent_group_id(
            dstn_parent_id) if not self.airgap else True
        if self.dstn_parent_group_path_validated_in_session:
            return dstn_parent_id
        self.dstn_parent_group_path_validated_in_session = self.validate_dstn_parent_group_path(
            self.prop("DESTINATION", "dstn_parent_group_path")) if not self.airgap else True
        return dstn_parent_id

    @property
    def import_user_id(self):
        import_user_id = self.prop_int("DESTINATION", "import_user_id")
        if self.import_user_id_validated_in_session:
            return import_user_id
        self.import_user_id_validated_in_session = self.validate_import_user_id(
            import_user_id)
        return import_user_id

    @property
    def dstn_parent_group_path(self):
        dstn_parent_group_path = self.prop(
            "DESTINATION", "dstn_parent_group_path")
        if self.dstn_parent_group_path_validated_in_session:
            return dstn_parent_group_path
        self.dstn_parent_group_path_validated_in_session = self.validate_dstn_parent_group_path(
            dstn_parent_group_path) if not self.airgap else True
        return dstn_parent_group_path

    @property
    def destination_token(self):
        dstn_token = self.prop(
            "DESTINATION", "dstn_access_token", default=None, obfuscated=True)
        if self.dstn_token_validated_in_session:
            return dstn_token
        # Air-gapped migrations w/ no access to destination
        self.dstn_token_validated_in_session = self.validate_dstn_token(
            dstn_token) if not self.airgap else True
        return dstn_token

    @property
    def source_token(self):
        obfuscated = True
        if self.source_type == 'azure devops':
            obfuscated = False
        src_token = self.prop("SOURCE", "src_access_token",
                              default=None, obfuscated=obfuscated)
        if self.src_token_validated_in_session:
            return src_token
        self.src_token_validated_in_session = self.validate_src_token(
            src_token) if not self.airgap else True
        return src_token

    @property
    def airgap(self):
        if ag := self.prop_bool("APP", "airgap", default=False):
            if self.airgap_validated_in_session:
                return ag
            try:
                return self.validate_airgap_configuration()
            except ConfigurationException as ce:
                sys.exit(ce)
        return False

    @property
    def direct_transfer(self):
        if direct_transfer := self.prop_bool("APP", "direct_transfer", default=False):
            if self.direct_transfer_validated_in_session:
                return direct_transfer
            try:
                return self.validate_direct_transfer_enabled()
            except ConfigurationException as ce:
                sys.exit(ce)
        return False

    def validate_dstn_parent_group_id(self, pgid):
        if pgid is not None:
            group_resp = safe_json_response(self.groups.get_group(
                pgid, self.destination_host, self.destination_token))
            error, group_resp = is_error_message_present(group_resp)
            if error or not group_resp:
                raise ConfigurationException("parent_id")
            return True
        return True

    def validate_import_user_id(self, iuid):
        if iuid is not None:
            user_resp = safe_json_response(self.users.get_user(
                iuid, self.destination_host, self.destination_token))
            is_error, user_resp = is_error_message_present(user_resp)
            if is_error or not user_resp:
                raise ConfigurationException("import_user_id")
            if user_resp.get("error") is not None:
                if user_resp["error"] == "invalid_token":
                    raise ConfigurationException(
                        "parent_token", msg=f"{json_pretty(user_resp)}")
                raise Exception(user_resp)
            if user_resp["id"] == iuid:
                return True
        raise ConfigurationException("import_user_id")

    def validate_dstn_parent_group_path(self, dstn_parent_group_path):
        if dstn_parent_group_path is not None:
            group_resp = safe_json_response(self.groups.get_group(
                self.prop_int("DESTINATION", "dstn_parent_group_id"),
                self.destination_host,
                self.destination_token))
            error, group_resp = is_error_message_present(group_resp)
            if error or not group_resp:
                raise ConfigurationException(
                    "dstn_parent_group_path", msg=f"Invalid dest parent group param:\n{json_pretty(group_resp)}")
            group_full_path = group_resp["full_path"]
            if group_full_path == dstn_parent_group_path:
                if group_resp["visibility"] == "public":
                    raise ConfigurationException(
                        "dstn_parent_group_path", msg=f"Public destination parent group: {group_full_path}. Please set visibility to 'internal' or 'private'")
            else:
                raise ConfigurationException(
                    "dstn_parent_group_path", msg=f"Destination group in config [{dstn_parent_group_path}] does not match group path from API response [{group_full_path}] Please correct configuration settings")
            return True
        return True

    def validate_dstn_token(self, dstn_token):
        if dstn_token is not None:
            user = safe_json_response(self.users.get_current_user(
                self.destination_host, dstn_token))
            is_error, user = is_error_message_present(user)
            # Admin token required when migrating from GitLab
            if is_error or not user:
                raise ConfigurationException(
                    "destination_token", msg=f"Invalid user and/or token:\n{json_pretty(user)}")
            is_admin = user.get(
                "is_admin") if self.source_type == "gitlab" else True
            if not is_admin:
                print(
                    "Destination token is currently assigned to a non-admin user. Some API endpoints (e.g. users) may be forbidden")
            return True
        return True

    def validate_src_token(self, src_token):
        if src_token:
            user = None
            err_msg = "Invalid user and/or token:\n"
            if self.source_type == "gitlab":
                self.validate_src_token_gitlab(user, err_msg, src_token)
            elif self.source_type == "github":
                self.validate_src_token_github(user, err_msg, src_token)
            elif self.source_type == "bitbucket server":
                self.validate_src_token_bitbucket(user, err_msg, src_token)
            elif self.source_type == "azure devops":
                self.validate_src_token_ado(err_msg, src_token)
            return True
        return True

    def validate_src_token_gitlab(self, user, msg, token):
        user = safe_json_response(
            self.users.get_current_user(self.source_host, token))
        is_error, user = is_error_message_present(user)
        if is_error or not user:
            raise ConfigurationException(
                "source_token", msg=f"{msg}{json_pretty(user)}")
        if not user.get("is_admin"):
            print("Source token is currently assigned to a non-admin user. Some API endpoints (e.g. users) may be forbidden")

    def validate_src_token_github(self, user, msg, token):
        gh_dot_com = is_github_dot_com(self.source_host)

        if "github.com" in self.source_host and not gh_dot_com:
            raise ConfigurationException(
                "src_hostname", msg=f"{msg}GitHub.com source requires 'https://api.github.com' as the 'src_hostname' in 'data/congregate.conf'")

        user = safe_json_response(requests.get(
            f"{self.source_host.rstrip('/')}/user" if gh_dot_com
            else f"{self.source_host}/api/v3/user",
            params={},
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {token}"
            },
            verify=self.ssl_verify,
            timeout=self.GET_TIMEOUT))
        is_error, user = is_error_message_present(user)
        if not user or is_error or (not user.get(
                "site_admin") and not gh_dot_com):
            raise ConfigurationException(
                "source_token", msg=f"{msg}{json_pretty(user)}")

    def validate_src_token_bitbucket(self, user, msg, token):
        username = self.source_username
        host = self.source_host
        auth = f"{username}:{token}".encode("ascii")
        ssl = self.ssl_verify
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {b64encode(auth).decode('ascii')}"
        }
        # Lookup User access rights
        user = safe_json_response(requests.get(
            f"{host}/rest/api/1.0/admin/permissions/users?filter={username}",
            params={},
            headers=headers,
            verify=ssl,
            timeout=self.GET_TIMEOUT)
        )
        is_admin = user["values"][0]["permission"] in [
            "SYS_ADMIN", "ADMIN"] if (user and user.get("values")) else False
        if not is_admin and user and user.get("values") == []:
            # Lookup Group access rights
            user = safe_json_response(requests.get(
                f"{host}/rest/api/1.0/admin/users/more-members?context={username}",
                params={},
                headers=headers,
                verify=ssl,
                timeout=self.GET_TIMEOUT)
            )
            group_name = user["values"][0]["name"] if (
                user and user.get("values", [])) else None
            if group_name:
                group = safe_json_response(requests.get(
                    f"{host}/rest/api/1.0/admin/permissions/groups?filter={group_name}",
                    params={},
                    headers=headers,
                    verify=ssl,
                    timeout=self.GET_TIMEOUT)
                )
                is_admin = group["values"][0]["permission"] in ["SYS_ADMIN", "ADMIN"] if (
                    group and group.get("values", [])) else False
        is_error, user = is_error_message_present(user)
        if not user or is_error or not is_admin:
            raise ConfigurationException(
                "source_token", msg=f"{msg}{json_pretty(user)}")

    def validate_src_token_ado(self, msg, token):

        ssl = self.ssl_verify
        source_host = self.source_host
        ado_api_version = self.ado_api_version
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(
            f"{source_host}/_apis/ConnectionData",
            headers=headers,
            params={'api-version': ado_api_version},
            verify=ssl,
            timeout=self.GET_TIMEOUT
        )

        if response.status_code == 200:
            connection_data = response.json()
            if connection_data.get('authenticatedUser'):
                return True
            else:
                raise ConfigurationException(
                    "source_token", msg=f"{msg}Invalid user authentication:\n{json_pretty(connection_data)}")

    def validate_airgap_configuration(self):
        airgap_export = self.prop_bool("APP", "airgap_export", default=False)
        airgap_import = self.prop_bool("APP", "airgap_import", default=False)
        if airgap_export and airgap_import:
            raise ConfigurationException(
                'airgap', msg="Invalid configuration. Air-gap export and import both set to True. Only one can be enabled at a time")
        if not (airgap_export or airgap_import):
            raise ConfigurationException(
                'airgap', msg="Invalid configuration. Air-gap is enabled but neither airgap_export nor airgap_import is enabled. Set one of them to True"
            )
        return True

    def validate_direct_transfer_enabled(self):
        src_gitlab_dot_com = is_dot_com(self.source_host)
        dest_gitlab_dot_com = is_dot_com(self.destination_host)
        src_bulk_import, src_max_download = self.__get_dt_configuration(
            self.source_host, self.source_token, src_gitlab_dot_com)
        dest_bulk_import, dest_max_download = self.__get_dt_configuration(
            self.destination_host, self.destination_token, dest_gitlab_dot_com)
        if src_bulk_import is None:
            print("Warning: Cannot confirm bulk import is enabled on source. This could be due to using a regular user personal access token. See docs: https://docs.gitlab.com/ee/api/settings.html#get-current-application-settings")
        if dest_bulk_import is None:
            print("Warning: Cannot confirm bulk import is enabled on destination. This could be due to using a regular user personal access token. See docs: https://docs.gitlab.com/ee/api/settings.html#get-current-application-settings")
        if src_bulk_import and dest_bulk_import:
            if src_max_download == dest_max_download:
                return True
            else:
                print(
                    f"Warning: bulk_import_max_download_file_size does not match on source (max {src_max_download}) and destination (max {dest_max_download}). Update settings if possible. See docs: See docs: https://docs.gitlab.com/ee/api/settings.html#change-application-settings")
        elif dest_bulk_import is False:
            # Assuming admin privileges and can officially confirm direct transfer is disabled
            raise ConfigurationException(
                'direct_transfer', f"Direct transfer is not enabled on the destination instance. Please enable it in the admin settings. See docs: https://docs.gitlab.com/ee/administration/settings/import_and_export_settings.html#enable-migration-of-groups-and-projects-by-direct-transfer"
            )
        elif src_bulk_import is False:
            raise ConfigurationException(
                'direct_transfer', f"Direct transfer is not enabled on the source instance. Please enable it in the admin settings. See docs: https://docs.gitlab.com/ee/administration/settings/import_and_export_settings.html#enable-migration-of-groups-and-projects-by-direct-transfer"
            )
        elif not (src_bulk_import or dest_bulk_import):
            raise ConfigurationException(
                'direct_transfer', f"Cannot confirm if bulk import is enabled on either source or destination. This is likely due to using standard user access tokens on both self-managed instances. Please use an admin token for at least the source instance"
            )
        return True

    def __get_dt_configuration(self, host, token, dot_com):
        if not dot_com:
            instance_api = InstanceApi()
            settings = safe_json_response(instance_api.get_application_settings(
                host, token))
            if settings:
                # Return actual settings from the API
                return self.__get_bulk_import_settings(
                    settings)
            else:
                # Return an empty tuple since we can't get a valid response
                return (None, None)
        else:
            # Return default values
            return True, 5120

    def __get_bulk_import_settings(self, settings):
        return (settings.get("bulk_import_enabled", False),
                settings.get("bulk_import_max_download_file_size", False))

    @property
    def dstn_parent_id_validated_in_session(self):
        return self._dstn_parent_id_validated_in_session

    @property
    def import_user_id_validated_in_session(self):
        return self._import_user_id_validated_in_session

    @property
    def dstn_parent_group_path_validated_in_session(self):
        return self._dstn_parent_group_path_validated_in_session

    @property
    def dstn_token_validated_in_session(self):
        return self._dstn_token_validated_in_session

    @property
    def src_token_validated_in_session(self):
        return self._src_token_validated_in_session

    @property
    def airgap_validated_in_session(self):
        return self._airgap_validated_in_session

    @property
    def direct_transfer_validated_in_session(self):
        return self._direct_transfer_validated_in_session

    @dstn_parent_id_validated_in_session.setter
    def dstn_parent_id_validated_in_session(self, value):
        self._dstn_parent_id_validated_in_session = value

    @import_user_id_validated_in_session.setter
    def import_user_id_validated_in_session(self, value):
        self._import_user_id_validated_in_session = value

    @dstn_parent_group_path_validated_in_session.setter
    def dstn_parent_group_path_validated_in_session(self, value):
        self._dstn_parent_group_path_validated_in_session = value

    @dstn_token_validated_in_session.setter
    def dstn_token_validated_in_session(self, value):
        self._dstn_token_validated_in_session = value

    @src_token_validated_in_session.setter
    def src_token_validated_in_session(self, value):
        self._src_token_validated_in_session = value

    @airgap_validated_in_session.setter
    def airgap_validated_in_session(self, value):
        self._airgap_validated_in_session = value

    @direct_transfer_validated_in_session.setter
    def direct_transfer_validated_in_session(self, value):
        self._direct_transfer_validated_in_session = value
