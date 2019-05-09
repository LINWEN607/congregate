from flask import Flask

app = Flask(__name__)

from . import views
from . import models
from . import controllers
import os
import logging

from helpers import logger as log
from helpers.base_module import app_path

l = log.congregate_logger('werkzeug')

l.logger.setLevel(logging.ERROR)