"""
Base class to import congregate configuration
and logger as well provide the app path
"""

from warnings import simplefilter
from urllib3.exceptions import InsecureRequestWarning
from congregate.helpers.configuration_validator import ConfigurationValidator
from gitlab_ps_utils.logger import myLogger
from gitlab_ps_utils.audit_logger import audit_logger
from congregate.helpers.utils import get_congregate_path
from gitlab_ps_utils.processes import MultiProcessing


class BaseClass(object):
    def __init__(self):
        self.config = ConfigurationValidator()
        if not self.config.ssl_verify:
            simplefilter("ignore", category=InsecureRequestWarning)
        self.app_path = get_congregate_path()
        self.log_name = 'congregate'
        self.log = myLogger(__name__, app_path=self.app_path,
                            log_name=self.log_name, config=self.config)
        self.audit = audit_logger(__name__, app_path=self.app_path)
        self.INACTIVE = ["blocked", "ldap_blocked", "deactivated", "banned"]
        self.multi = MultiProcessing()
