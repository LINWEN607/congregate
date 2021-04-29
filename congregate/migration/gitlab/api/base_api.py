from congregate.helpers.logger import myLogger
from congregate.helpers.audit_logger import audit_logger
from congregate.helpers.utils import get_congregate_path
from congregate.helpers.api import GitLabApi

class GitLabApiWrapper():
    def __init__(self):
        self.app_path = get_congregate_path()
        self.log_name = 'congregate'
        self.log = myLogger(__name__, app_path=self.app_path, log_name=self.log_name)
        self.audit = audit_logger(__name__, app_path=self.app_path)
        self.api = GitLabApi(app_path=self.app_path, log_name=self.log_name)