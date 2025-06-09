from gitlab_ps_utils.logger import myLogger
from gitlab_ps_utils.audit_logger import audit_logger
from congregate.migration.gitlab.api import glapi, log_name, app_path


class GitLabApiWrapper():
    api = glapi
    def __init__(self):
        self.log = myLogger(
            __name__,
            app_path=app_path,
            log_name=log_name)
        self.audit = audit_logger(__name__, app_path=app_path)


