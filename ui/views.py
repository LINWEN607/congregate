from flask import render_template
from flask import Response
from flask import stream_with_context
from . import app
from models import get_data
import time


@app.route("/")
@app.route("/home")
def home_page():
    return render_template("index.html")

@app.route("/projects")
def project_page():
    data = get_data("project_json")
    return render_template("projects.html", data=data)

@app.route("/users")
def user_page():
    data = get_data("users")
    return render_template("users.html", data=data)

@app.route("/groups")
def group_page():
    data = get_data("groups")
    return render_template("groups.html", data=data)

@app.route("/config")
def config_page():
    data = dict(get_data("config"))
    print data
    return render_template("config.html", data=data)

@app.route('/large')
def generate_stream():
    def generate():
        for x in range(0, 100):
            time.sleep(0.5)
            yield str(x)
    return Response(stream_with_context(generate()))