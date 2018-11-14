from flask import Flask
app = Flask(__name__)

from . import views
from . import models
import os

import logging

try:
    from helpers import logger as log
except ImportError:
    from congregate.helpers import logger as log

app_path = os.getenv("CONGREGATE_PATH")

l = log.congregate_logger('werkzeug')

l.logger.setLevel(logging.ERROR)