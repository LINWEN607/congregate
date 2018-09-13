from flask import render_template
from . import app
from . import models

@app.route("/")
@app.route("/home")
def home_page():
    return render_template("index.html")

@app.route("/projects")
def project_page():
    data = models.get_data("project_json")
    return render_template("projects.html", data=data)

@app.route("/users")
def user_page():
    data = models.get_data("users")
    return render_template("users.html", data=data)

@app.route("/groups")
def group_page():
    data = models.get_data("groups")
    return render_template("groups.html", data=data)

@app.route("/config")
def config_page():
    data = dict(models.get_data("config"))
    print data
    return render_template("config.html", data=data)