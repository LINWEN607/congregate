"""
Base class to import congregate configuration
and logger as well provide the app path
"""

from warnings import simplefilter
from urllib3.exceptions import InsecureRequestWarning
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.helpers.logger import myLogger
from congregate.helpers.audit_logger import audit_logger
from congregate.helpers.utils import get_congregate_path


class BaseClass(object):
    def __init__(self):
        self.config = ConfigurationValidator()
        if not self.config.ssl_verify:
            simplefilter("ignore", category=InsecureRequestWarning)
        self.app_path = get_congregate_path()
        self.log_name = 'congregate'
        self.log = myLogger(__name__, app_path=self.app_path, log_name=self.log_name, config=self.config)
        self.audit = audit_logger(__name__, app_path=self.app_path)
        self.BLOCKED = ["blocked", "ldap_blocked", "deactivated"]
