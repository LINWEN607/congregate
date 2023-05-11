from congregate.helpers.base_class import BaseClass

class BaseGitLabClient(BaseClass):
    """
        Base client class for GitLab features

        Primarily used to set the source host and token
        on initialization to be used for airgapped migrations
    """
    def __init__(self, src_host=None, src_token=None):
        super().__init__()
        self.src_host = self.__get_property(src_host, self.config.source_host)
        self.src_token = self.__get_property(src_token, self.config.source_token)

    def __get_property(self, val, default):
        if val:
            return val
        return default
    
