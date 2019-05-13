'''

Base class to import congregate configuration
and logger as well provide the app path

'''

from os import getenv
from helpers import conf
from helpers.logger import myLogger


class BaseClass(object):
    def __init__(self):
        self.config = conf.ig()
        self.log = myLogger(__name__)
        self.app_path = getenv("CONGREGATE_PATH")