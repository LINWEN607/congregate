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
        self.log = myLogger(__name__)
        self.audit = audit_logger(__name__)
        self.app_path = get_congregate_path()
        self.BLOCKED = ["blocked", "ldap_blocked", "deactivated"]
