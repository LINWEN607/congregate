"""
Base module to import congregate configuration
and logger as well provide the app path
"""

from congregate.helpers.logger import myLogger
from congregate.helpers.audit_logger import audit_logger
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.helpers.misc_utils import get_congregate_path

if __name__ == "__main__":
    log = myLogger(__name__)
    audit_log = audit_logger(__name__)
    app_path = get_congregate_path()
    config = ConfigurationValidator()
