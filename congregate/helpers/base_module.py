'''

Base module to import congregate configuration
and logger as well provide the app path

'''

from os import getenv
from helpers.logger import myLogger
from helpers import conf

log = myLogger(__name__)
app_path = getenv("CONGREGATE_PATH")
config = conf.ig()
