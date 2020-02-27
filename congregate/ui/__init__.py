###
### If this file is changed due to autopep8, revert the change or else the UI won't load
###
import os
import sys
import logging
from flask import Flask

app = Flask(__name__)

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)))))

from . import controllers
from . import models
from . import views

from congregate.helpers.logger import myLogger


log = myLogger('werkzeug')

log.setLevel(logging.ERROR)
