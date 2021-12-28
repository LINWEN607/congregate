from gitlab_ps_utils.logger import myLogger
from gitlab_ps_utils.audit_logger import audit_logger
from congregate.helpers.utils import get_congregate_path
from gitlab_ps_utils.api import GitLabApi
from congregate.helpers.conf import Config

class GitLabApiWrapper():
    def __init__(self):
        self.app_path = get_congregate_path()
        self.log_name = 'congregate'
        self.log = myLogger(__name__, app_path=self.app_path, log_name=self.log_name)
        self.audit = audit_logger(__name__, app_path=self.app_path)
        self.config = Config()
        self.api = GitLabApi(app_path=self.app_path, log_name=self.log_name, ssl_verify=self.config.ssl_verify)
        
