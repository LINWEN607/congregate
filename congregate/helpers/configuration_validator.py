from congregate.helpers.exceptions import ConfigurationException
from congregate.helpers.conf import ig
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi

class ConfigurationValidator(ig):
    '''
        Extended config class used to validate the configuration on run
    '''
    def __init__(self):
        self.groups = GroupsApi()
        self.users = UsersApi()
        self.parent_id_validated_in_session = False
        self.parent_user_id_validated_in_session = False
        super(ConfigurationValidator, self).__init__()

    @property
    def parent_id(self):
        parent_id = self.config.get("parent_id", None)
        if self.parent_id_validated_in_session is True:
            return parent_id
        else:
            self.parent_id_validated_in_session = self.validate_parent_group_id(parent_id)
            return parent_id

    @property
    def parent_user_id(self):
        parent_user_id = self.config.get("parent_user_id", None)
        if self.parent_user_id_validated_in_session is True:
            return parent_user_id
        else:
            self.parent_user_id_validated_in_session = self.validate_parent_user_id(parent_user_id)
            return parent_user_id

    def validate_parent_group_id(self, id):
        if id is not None:
            group_resp = self.groups.get_group(id, self.parent_host, self.parent_token).json()
            if group_resp.get("message", None) is not None:
                raise ConfigurationException("parent_id")
            else:
                return True
        else:
            return True

    def validate_parent_user_id(self, id):
        if id is None:
            raise ConfigurationException("parent_user_id")
        else:
            user_resp = self.users.get_current_user(self.parent_host, self.parent_token).json()
            if user_resp.get("message", None) is not None:
                raise ConfigurationException("parent_user_id")
            elif user_resp.get("error", None) is not None:
                if user_resp["error"] == "invalid_token":
                    raise ConfigurationException("parent_token")
                else:
                    raise Exception
            else:
                if user_resp["id"] == id:
                    return True
                else:
                    raise ConfigurationException("parent_user_id")