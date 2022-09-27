"""
Base class to import congregate configuration
and logger as well provide the app path
"""
import os
import sys

from warnings import simplefilter
from urllib3.exceptions import InsecureRequestWarning

from gitlab_ps_utils.logger import myLogger
from gitlab_ps_utils.audit_logger import audit_logger
from gitlab_ps_utils.processes import MultiProcessing

from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.helpers.utils import get_congregate_path


class BaseClass():
    TANUKI = "#e24329"
    DESC = "Progress"
    UNIT = " unit"

    def __init__(self):
        self.config = ConfigurationValidator()
        if not self.config.ssl_verify:
            simplefilter("ignore", category=InsecureRequestWarning)
        self.app_path = get_congregate_path()
        self.log_name = 'congregate'
        self.log = myLogger(__name__, app_path=self.app_path,
                            log_name=self.log_name, config=self.config)
        self.audit = audit_logger(__name__, app_path=self.app_path)
        self.INACTIVE = ["blocked", "blocked_pending_approval",
                         "ldap_blocked", "deactivated", "banned"]
        self.multi = MultiProcessing()

    def check_list_subset_input_file_path(self):
        subset_path = self.config.list_subset_input_path
        if not os.path.isfile(subset_path):
            self.log.error(
                f"Config 'list_subset_input_path' file path '{subset_path}' does not exist. Please create it")
            sys.exit(os.EX_CONFIG)
        return subset_path
