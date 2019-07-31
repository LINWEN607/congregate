from congregate.helpers.exceptions import ConfigurationException
from congregate.helpers.conf import ig
from congregate.migration.gitlab.groups import GroupsClient as groups_client

class ConfigurationValidator(ig):
    '''
        Extended config class used to validate the configuration on run
    '''
    def __init__(self):
        self.groups = groups_client()
        self.parent_id_validated_in_session = False
        super(ConfigurationValidator, self).__init__()

    @property
    def parent_id(self):
        parent_id = self.config.get("parent_id", None)
        if self.parent_id_validated_in_session is True:
            return parent_id
        else:
            self.parent_id_validated_in_session = self.validate_parent_group_id(parent_id)
            return parent_id

    def validate_parent_group_id(self, id):
        if id is not None:
            group_resp = self.groups.get_group(id, self.parent_host, self.parent_token).json()
            if group_resp.get("message", None) is not None:
                raise ConfigurationException("parent_id")
            else:
                return True
        else:
            return True
