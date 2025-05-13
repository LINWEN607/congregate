"""
Base class to import congregate configuration
and logger as well provide the app path
"""
from logging import FileHandler
from os.path import exists
from warnings import simplefilter
from urllib3.exceptions import InsecureRequestWarning
from pythonjsonlogger.json import JsonFormatter

from gitlab_ps_utils.logger import myLogger
from gitlab_ps_utils.audit_logger import audit_logger
from gitlab_ps_utils.processes import MultiProcessing

from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.helpers.utils import get_congregate_path
from congregate.helpers.syslog_filter import SyslogLevelFilter



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
        self.log = self.set_up_logger(__name__)
        self.audit = audit_logger(__name__, app_path=self.app_path)
        self.INACTIVE = ["blocked", "blocked_pending_approval",
                         "ldap_blocked", "deactivated", "banned"]
        self.multi = MultiProcessing()

    def set_up_logger(self, logger_name):
        base_logger = myLogger(logger_name, app_path=self.app_path, log_name=self.log_name, config=self.config)
        for handler in base_logger.handlers:
            if '.json' in handler.__dict__.get('baseFilename', ''):
                return base_logger
        json_log_format = "{created}{syslog_level}{module}{funcName}{lineno}{message}{filename}"
        syslog_filter = SyslogLevelFilter(min_syslog_level=7)  # Allow all levels
        base_logger.addFilter(syslog_filter)
        gelf_formatting = {
            "created": "timestamp",
            "lineno": "line",
            "syslog_level": "level",
            "exc_info": "full_message",
            "message": "short_message",
            "filename": "file",
            "module": "_module",
            "funcName": "_function",
        }

        formatter = JsonFormatter(
            json_log_format, 
            style="{",
            rename_fields=gelf_formatting,
            defaults={"version": "1.1"}
        )
        log_dir = f'{self.app_path}/data/logs'
        if exists(log_dir):
            log_path = f'{log_dir}/congregate_log.json'
            json_log_handler = FileHandler(log_path)
            json_log_handler.setFormatter(formatter)
            json_log_handler.setLevel(2)
            base_logger.addHandler(json_log_handler)
        return base_logger
