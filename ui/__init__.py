from flask import Flask
app = Flask(__name__)

from . import views
from . import models

import logging, os

app_path = os.getenv("CONGREGATE_PATH")
logging.basicConfig(filename='%s/congregate.log' % app_path, level=logging.INFO)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)