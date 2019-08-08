"""
Base class to import congregate configuration
and logger as well provide the app path
"""

from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.helpers.logger import myLogger
from congregate.helpers.misc_utils import get_congregate_path


class BaseClass(object):
    def __init__(self):
        self.config = ConfigurationValidator()
        self.log = myLogger(__name__)
        self.app_path = get_congregate_path()
