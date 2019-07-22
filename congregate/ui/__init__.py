from flask import Flask
import os
import sys

app = Flask(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from . import views
from . import models
from . import controllers

import logging

from congregate.helpers.logger import myLogger
# from congregate.helpers.base_module import app_path

log = myLogger('werkzeug')

log.setLevel(logging.ERROR)
