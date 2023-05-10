from congregate.helpers.base_class import BaseClass

class BaseGitLabClient(BaseClass):
    """
        Base client class for GitLab features

        Primarily used to set the source host and token
        on initialization to be used for airgapped migrations
    """
    def __init__(self, src_host=None, src_token=None):
        super().__init__()
        self.__set_property('__src_host', src_host, self.config.source_host)
        self.__set_property('__src_token', src_token, self.config.source_token)

    def __set_property(self, prop, val, default):
        if val:
            setattr(self, prop, val)
        else:
            setattr(self, prop, default)
    
    @property
    def src_host(self):
        """
            Source GitLab host URL

            Defaults to source host defined in config,
            but can be overridden on client initialization
        """
        return self.__src_host
    
    @property
    def src_token(self):
        """
            Source GitLab access token

            Defaults to source token defined in config,
            but can be overridden on client initialization
        """
        return self.__src_token
