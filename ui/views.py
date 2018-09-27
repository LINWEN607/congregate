from flask import render_template, Response, stream_with_context, send_from_directory
from . import app
from models import get_data, get_counts
import time


@app.route("/")
@app.route("/home")
def home_page():
    data = get_counts()
    return render_template("index.html", data=data)

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
    return render_template("config.html", data=data)

@app.route('/base/<path:filename>')
def base_static(filename):
    return send_from_directory(app.root_path + '/../js-packages/', filename)

@app.route('/large')
def generate_stream():
    def generate():
        for x in range(0, 100):
            time.sleep(0.5)
            yield str(x)
    return Response(stream_with_context(generate()))