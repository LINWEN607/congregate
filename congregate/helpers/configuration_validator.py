from congregate.helpers.exceptions import ConfigurationException
from congregate.helpers.conf import Config
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.helpers.misc_utils import is_error_message_present, safe_json_response


class ConfigurationValidator(Config):
    '''
    Extended config class used to validate the configuration on run
    '''
    def __init__(self, path=None):
        self.groups = GroupsApi()
        self.users = UsersApi()
        self.instance = InstanceApi()
        self._dstn_parent_id_validated_in_session = False
        self._import_user_id_validated_in_session = False
        self._dstn_parent_group_path_validated_in_session = False
        self._dstn_token_validated_in_session = False
        self._src_token_validated_in_session = False
        super(ConfigurationValidator, self).__init__(path=path)

    @property
    def dstn_parent_id(self):
        dstn_parent_id = self.prop_int("DESTINATION", "dstn_parent_group_id")
        if self.dstn_parent_id_validated_in_session is True:
            return dstn_parent_id
        else:
            self.dstn_parent_id_validated_in_session = self.validate_dstn_parent_group_id(dstn_parent_id)
            if self.dstn_parent_group_path_validated_in_session is True:
                return dstn_parent_id
            self.dstn_parent_group_path_validated_in_session = self.validate_dstn_parent_group_path(self.prop("DESTINATION", "dstn_parent_group_path"))
            return dstn_parent_id

    @property
    def import_user_id(self):
        import_user_id = self.prop_int("DESTINATION", "import_user_id")
        if self.import_user_id_validated_in_session is True:
            return import_user_id
        self.import_user_id_validated_in_session = self.validate_import_user_id(import_user_id)
        return import_user_id

    @property
    def dstn_parent_group_path(self):
        dstn_parent_group_path = self.prop("DESTINATION", "dstn_parent_group_path")
        if self.dstn_parent_group_path_validated_in_session is True:
            return dstn_parent_group_path
        self.dstn_parent_group_path_validated_in_session = self.validate_dstn_parent_group_path(dstn_parent_group_path)
        return dstn_parent_group_path

    @property
    def destination_token(self):
        dstn_token = self.prop("DESTINATION", "dstn_access_token", default=None, obfuscated=True)
        if self.dstn_token_validated_in_session is True:
            return dstn_token
        self.dstn_token_validated_in_session = self.validate_dstn_token(dstn_token)
        return dstn_token

    @property
    def source_token(self):
        src_token = self.prop("SOURCE", "src_access_token", default=None, obfuscated=True)
        if self.src_token_validated_in_session is True:
            return src_token
        self.src_token_validated_in_session = self.validate_src_token(src_token)
        return src_token

    def validate_dstn_parent_group_id(self, pgid):
        if pgid is not None:
            group_resp = safe_json_response(self.groups.get_group(pgid, self.destination_host, self.destination_token))
            if is_error_message_present(group_resp):
                raise ConfigurationException("parent_id")
            else:
                return True
        return True

    def validate_import_user_id(self, iuid):
        if iuid is not None:
            user_resp = self.users.get_current_user(self.destination_host, self.destination_token)
            if is_error_message_present(user_resp):
                raise ConfigurationException("import_user_id")
            elif user_resp.get("error", None) is not None:
                if user_resp["error"] == "invalid_token":
                    raise ConfigurationException("parent_token")
                else:
                    raise Exception
            else:
                if user_resp["id"] == iuid:
                    return True
        raise ConfigurationException("import_user_id")

    def validate_dstn_parent_group_path(self, dstn_parent_group_path):
        if dstn_parent_group_path is not None:
            group_resp = safe_json_response(self.groups.get_group(
                self.prop_int("DESTINATION", "dstn_parent_group_id"),
                self.destination_host,
                self.destination_token))
            if group_resp["full_path"] == dstn_parent_group_path:
                return True
            raise ConfigurationException("dstn_parent_group_path")
        return True

    def validate_dstn_token(self, dstn_token):
        if dstn_token is not None:
            license_resp = self.instance.get_current_license(self.destination_host, dstn_token)
            if not license_resp.ok:
                raise ConfigurationException("destination_token", msg=safe_json_response(license_resp))
        return True

    def validate_src_token(self, src_token):
        if src_token is not None:
            license_resp = self.instance.get_current_license(self.source_host, src_token)
            if not license_resp.ok:
                raise ConfigurationException("source_token", msg=safe_json_response(license_resp))
        return True

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
