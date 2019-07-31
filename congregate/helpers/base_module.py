"""
Base module to import congregate configuration
and logger as well provide the app path
"""

from congregate.helpers.logger import myLogger
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.helpers.misc_utils import get_congregate_path

log = myLogger(__name__)
app_path = get_congregate_path()
config = ConfigurationValidator()
