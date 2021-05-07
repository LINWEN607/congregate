from congregate.helpers.base_class import BaseClass
# from congregate.helpers.logger import myLogger
# from congregate.helpers.audit_logger import audit_logger
# from congregate.helpers.utils import get_congregate_path
from congregate.helpers.api import GitLabApi

class GitLabApiWrapper(BaseClass):
    def __init__(self):
        # self.app_path = get_congregate_path()
        # self.log_name = 'congregate'
        # self.log = myLogger(__name__, app_path=self.app_path, log_name=self.log_name)
        # self.audit = audit_logger(__name__, app_path=self.app_path)
        super().__init__()
        self.api = GitLabApi(app_path=self.app_path, log_name=self.log_name, ssl_verify=self.config.ssl_verify)
        
