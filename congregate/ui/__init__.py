from congregate.helpers.logger import myLogger
import logging
from . import controllers
from . import models
from . import views
from flask import Flask
import os
import sys

app = Flask(__name__)

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)))))


log = myLogger('werkzeug')

log.setLevel(logging.ERROR)
