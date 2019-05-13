from flask import Flask

app = Flask(__name__)

from . import views
from . import models
from . import controllers
import os
import logging

from helpers.logger import myLogger
from helpers.base_module import app_path

log = myLogger('werkzeug')

log.setLevel(logging.ERROR)