from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper


class BaseGitLabApiClient(BaseClass):
    def __init__(self):
        super(BaseGitLabApiClient, self).__init__()
        GitLabApiWrapper.ssl_verify = self.config.ssl_verify