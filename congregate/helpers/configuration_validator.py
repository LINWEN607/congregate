from congregate.helpers.exceptions import ConfigurationException
from congregate.helpers.conf import Config
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.helpers.misc_utils import is_error_message_present


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

    def validate_dstn_parent_group_id(self, pgid):
        if pgid is not None:
            group_resp = self.groups.get_group(pgid, self.destination_host, self.destination_token).json()
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
            group_resp = self.groups.get_group(
                self.prop_int("DESTINATION", "dstn_parent_group_id"),
                self.destination_host,
                self.destination_token).json()
            if group_resp["full_path"] == dstn_parent_group_path:
                return True
            raise ConfigurationException("dstn_parent_group_path")
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

    @dstn_parent_id_validated_in_session.setter
    def dstn_parent_id_validated_in_session(self, value):
        self._dstn_parent_id_validated_in_session = value
    
    @import_user_id_validated_in_session.setter
    def import_user_id_validated_in_session(self, value):
        self._import_user_id_validated_in_session = value
    
    @dstn_parent_group_path_validated_in_session.setter
    def dstn_parent_group_path_validated_in_session(self, value):
        self._dstn_parent_group_path_validated_in_session = value
