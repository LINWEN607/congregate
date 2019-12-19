from congregate.helpers.exceptions import ConfigurationException
# from congregate.helpers.conf import ig
from congregate.helpers.conf import Config
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi


class ConfigurationValidator(Config):
    '''
    Extended config class used to validate the configuration on run
    '''
    def __init__(self):
        self.groups = GroupsApi()
        self.users = UsersApi()
        self._parent_id_validated_in_session = False
        self._import_user_id_validated_in_session = False
        self._parent_group_path_validated_in_session = False
        super(ConfigurationValidator, self).__init__()

    @property
    def parent_id(self):
        parent_id = self.prop_int("DESTINATION", "parent_group_id")
        if self.parent_id_validated_in_session is True:
            return parent_id
        else:
            self.parent_id_validated_in_session = self.validate_parent_group_id(parent_id)
            if self.parent_group_path_validated_in_session is True:
                return parent_id
            self.parent_group_path_validated_in_session = self.validate_parent_group_path(self.prop("DESTINATION", "parent_group_path"))
            return parent_id

    @property
    def import_user_id(self):
        import_user_id = self.prop_int("DESTINATION", "import_user_id")
        if self.import_user_id_validated_in_session is True:
            return import_user_id
        self.import_user_id_validated_in_session = self.validate_import_user_id(import_user_id)
        return import_user_id

    @property
    def parent_group_path(self):
        parent_group_path = self.prop("DESTINATION", "parent_group_path")
        if self.parent_group_path_validated_in_session is True:
            return parent_group_path
        self.parent_group_path_validated_in_session = self.validate_parent_group_path(parent_group_path)
        return parent_group_path

    def validate_parent_group_id(self, pid):
        if pid is not None:
            group_resp = self.groups.get_group(pid, self.destination_host, self.destination_token).json()
            if group_resp.get("message", None) is not None:
                raise ConfigurationException("parent_id")
            else:
                return True
        raise ConfigurationException("parent_id")

    def validate_import_user_id(self, iuid):
        if iuid is not None:
            user_resp = self.users.get_current_user(self.destination_host, self.destination_token)
            if user_resp.get("message", None) is not None:
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

    def validate_parent_group_path(self, parent_group_path):
        if parent_group_path is not None:
            group_resp = self.groups.get_group(
                self.prop_int("DESTINATION", "parent_group_id"),
                self.destination_host,
                self.destination_token).json()
            if group_resp["full_path"] == parent_group_path:
                return True
        raise ConfigurationException("parent_group_path")


    @property
    def parent_id_validated_in_session(self):
        return self._parent_id_validated_in_session

    @property
    def import_user_id_validated_in_session(self):
        return self._import_user_id_validated_in_session

    @property
    def parent_group_path_validated_in_session(self):
        return self._parent_group_path_validated_in_session

    @parent_id_validated_in_session.setter
    def parent_id_validated_in_session(self, value):
        self._parent_id_validated_in_session = value
    
    @import_user_id_validated_in_session.setter
    def import_user_id_validated_in_session(self, value):
        self._import_user_id_validated_in_session = value
    
    @parent_group_path_validated_in_session.setter
    def parent_group_path_validated_in_session(self, value):
        self._parent_group_path_validated_in_session = value


# class ConfigurationValidator(ig):
#     '''
#         Extended config class used to validate the configuration on run
#     '''
#     def __init__(self):
#         self.groups = GroupsApi()
#         self.users = UsersApi()
#         self._parent_id_validated_in_session = False
#         self._import_user_id_validated_in_session = False
#         self._parent_group_path_validated_in_session = False
#         super(ConfigurationValidator, self).__init__()

#     @property
#     def parent_id(self):
#         parent_id = self.config.get("parent_id", None)
#         if self.parent_id_validated_in_session is True:
#             return parent_id
#         else:
#             self.parent_id_validated_in_session = self.validate_parent_group_id(parent_id)
#             if self.parent_group_path_validated_in_session is True:
#                 return parent_id
#             self.parent_group_path_validated_in_session = self.validate_parent_group_path(self.config.get("parent_group_path", None))
#             return parent_id

#     @property
#     def import_user_id(self):
#         import_user_id = self.config.get("import_user_id", None)
#         if self.import_user_id_validated_in_session is True:
#             return import_user_id
#         else:
#             self.import_user_id_validated_in_session = self.validate_import_user_id(import_user_id)
#             return import_user_id

#     @property
#     def parent_group_path(self):
#         parent_group_path = self.config.get("parent_group_path", None)
#         if self.parent_group_path_validated_in_session is True:
#             return parent_group_path
#         else:
#             self.parent_group_path_validated_in_session = self.validate_parent_group_path(parent_group_path)
#             return parent_group_path

#     def validate_parent_group_id(self, id):
#         if id is not None:
#             group_resp = self.groups.get_group(id, self.destination_host, self.destination_token).json()
#             if group_resp.get("message", None) is not None:
#                 raise ConfigurationException("parent_id")
#             else:
#                 return True
#         else:
#             return True

#     def validate_import_user_id(self, id):
#         if id is None:
#             raise ConfigurationException("import_user_id")
#         else:
#             user_resp = self.users.get_current_user(self.destination_host, self.destination_token)
#             if user_resp.get("message", None) is not None:
#                 raise ConfigurationException("import_user_id")
#             elif user_resp.get("error", None) is not None:
#                 if user_resp["error"] == "invalid_token":
#                     raise ConfigurationException("parent_token")
#                 else:
#                     raise Exception
#             else:
#                 if user_resp["id"] == id:
#                     return True
#                 else:
#                     raise ConfigurationException("import_user_id")

#     def validate_parent_group_path(self, parent_group_path):
#         if parent_group_path is not None:
#             group_resp = self.groups.get_group(self.parent_id, self.destination_host, self.destination_token).json()
#             if group_resp["full_path"] == parent_group_path:
#                 return True
#             raise ConfigurationException("parent_group_path")
#         return True


#     @property
#     def parent_id_validated_in_session(self):
#         return self._parent_id_validated_in_session

#     @property
#     def import_user_id_validated_in_session(self):
#         return self._import_user_id_validated_in_session

#     @property
#     def parent_group_path_validated_in_session(self):
#         return self._parent_group_path_validated_in_session

#     @parent_id_validated_in_session.setter
#     def parent_id_validated_in_session(self, value):
#         self._parent_id_validated_in_session = value

#     @import_user_id_validated_in_session.setter
#     def import_user_id_validated_in_session(self, value):
#         self._import_user_id_validated_in_session = value

#     @parent_group_path_validated_in_session.setter
#     def parent_group_path_validated_in_session(self, value):
#         self._parent_group_path_validated_in_session = value
