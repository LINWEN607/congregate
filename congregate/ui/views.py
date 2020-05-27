from flask import render_template, send_from_directory

from congregate.ui.models import get_data, get_counts
# from congregate.ui.models import get_config
from . import app


@app.route("/")
@app.route("/home")
def home_page():
    return render_template("index.html")

