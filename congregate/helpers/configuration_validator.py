from base64 import b64encode
import requests

from gitlab_ps_utils.exceptions import ConfigurationException
from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response
from gitlab_ps_utils.json_utils import json_pretty
from congregate.helpers.conf import Config
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.helpers.utils import is_github_dot_com


class ConfigurationValidator(Config):
    '''
    Extended config class used to validate the configuration on run
    '''

    def __init__(self, path=None):
        self.groups = GroupsApi()
        self.users = UsersApi()
        self._dstn_parent_id_validated_in_session = False
        self._import_user_id_validated_in_session = False
        self._dstn_parent_group_path_validated_in_session = False
        self._dstn_token_validated_in_session = False
        self._src_token_validated_in_session = False
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
        self.dstn_token_validated_in_session = self.validate_dstn_token(
            dstn_token) if not self.airgap else True
        return dstn_token

    @property
    def source_token(self):
        src_token = self.prop("SOURCE", "src_access_token",
                              default=None, obfuscated=True)
        if self.src_token_validated_in_session:
            return src_token
        self.src_token_validated_in_session = self.validate_src_token(
            src_token) if not self.airgap else True
        return src_token

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
            error, user_resp = is_error_message_present(user_resp)
            if error or not user_resp:
                raise ConfigurationException("import_user_id")
            elif user_resp.get("error") is not None:
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
            elif group_resp["full_path"] == dstn_parent_group_path:
                return True
        return True

    def validate_dstn_token(self, dstn_token):
        if dstn_token is not None:
            user = safe_json_response(self.users.get_current_user(
                self.destination_host, dstn_token))
            error, user = is_error_message_present(user)
            if error or not user or not user.get("is_admin"):
                raise ConfigurationException(
                    "destination_token", msg=f"Invalid user and/or token:\n{json_pretty(user)}")
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
            return True
        return True

    def validate_src_token_gitlab(self, user, msg, token):
        user = safe_json_response(
            self.users.get_current_user(self.source_host, token))
        is_error, user = is_error_message_present(user)
        if not user or is_error or not user.get("is_admin"):
            raise ConfigurationException(
                "source_token", msg=f"{msg}{json_pretty(user)}")

    def validate_src_token_github(self, user, msg, token):
        user = safe_json_response(requests.get(
            f"{self.source_host.rstrip('/')}/user" if is_github_dot_com(
                self.source_host) else f"{self.source_host}/api/v3/user",
            params={},
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {token}"
            },
            verify=self.ssl_verify))
        is_error, user = is_error_message_present(user)
        if not user or is_error or (not user.get(
                "site_admin") and not is_github_dot_com(self.source_host)):
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
            verify=ssl)
        )
        is_admin = user["values"][0]["permission"] in [
            "SYS_ADMIN", "ADMIN"] if (user and user.get("values")) else False
        if not is_admin and user and user.get("values") == []:
            # Lookup Group access rights
            user = safe_json_response(requests.get(
                f"{host}/rest/api/1.0/admin/users/more-members?context={username}",
                params={},
                headers=headers,
                verify=ssl)
            )
            group_name = user["values"][0]["name"] if (
                user and user.get("values", [])) else None
            if group_name:
                group = safe_json_response(requests.get(
                    f"{host}/rest/api/1.0/admin/permissions/groups?filter={group_name}",
                    params={},
                    headers=headers,
                    verify=ssl)
                )
                is_admin = group["values"][0]["permission"] in ["SYS_ADMIN", "ADMIN"] if (
                    group and group.get("values", [])) else False
        is_error, user = is_error_message_present(user)
        if not user or is_error or not is_admin:
            raise ConfigurationException(
                "source_token", msg=f"{msg}{json_pretty(user)}")

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
