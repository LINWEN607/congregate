'''

Base module to import congregate configuration
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

config = conf.ig()
l = log.congregate_logger(__name__)
app_path = os.getenv("CONGREGATE_PATH")