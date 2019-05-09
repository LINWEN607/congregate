'''

Base module to import congregate configuration
and logger as well provide the app path

'''

from os import getenv
from helpers import logger as log
from helpers import conf

l = log.congregate_logger(__name__)
app_path = getenv("CONGREGATE_PATH")
config = conf.ig()

