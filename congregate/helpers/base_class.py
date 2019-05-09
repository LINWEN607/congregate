'''

Base class to import congregate configuration
and logger as well provide the app path

'''

import os
import json
try:
    from helpers import conf
    from helpers import logger as log
except ImportError:
    from congregate.helpers import conf
    from congregate.helpers import logger as log


class base_class():
    def __init__(self):
        self.config = conf.ig()
        self.l = log.congregate_logger(__name__)
        self.app_path = os.getenv("CONGREGATE_PATH")