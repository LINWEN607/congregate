from flask import render_template, Response, stream_with_context, send_from_directory
from . import app
from models import get_data, get_counts
#from time import sleep
import subprocess, os

app_path = os.getenv("CONGREGATE_PATH")

@app.route("/")
@app.route("/home")
def home_page():
    data = get_counts()
    return render_template("index.html", data=data)

@app.route("/projects")
def project_page():
    data = get_data("project_json", sort_by="namespace")
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

@app.route('/log')
def generate_stream():
    def generate():
        last_line = ""
        while True:
            output = subprocess.check_output(['tail', '-n 1', '%s/congregate.log' % app_path])
            if output == last_line:
                yield ""
            else:
                last_line = output
                yield "<p>" + output.split("|")[-1] + "</p>"
            subprocess.call(['sleep', '1'])

    return Response(stream_with_context(generate()))

@app.route('/logLine')
def return_last_line():
    output = subprocess.check_output(['tail', '-n 1', '%s/congregate.log' % app_path])
    return output.split(":")[-1]