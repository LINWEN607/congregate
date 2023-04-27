from flask import Flask, render_template
from congregate.cli.stage_projects import ProjectStageCLI
from congregate.cli.stage_groups import GroupStageCLI
from congregate.migration.gitlab.users import UsersClient
from congregate.ui.stage import StageAPI
from congregate.ui.test import TestAPI
from congregate.ui.models import data_retrieval
from congregate.ui.logs import logger

app = Flask(__name__,
            static_folder = "../../dist/assets",
            template_folder = "../../dist")

@app.route("/")
@app.route("/home")
def home_page():
    return render_template("index.html")

def register_api(app, api, client, name):
    asset = api.as_view(f"{name}", client, name)
    app.add_url_rule(f"/api/{api.route_prefix}/{name}/", view_func=asset)

register_api(app, StageAPI, ProjectStageCLI, 'projects')
register_api(app, StageAPI, GroupStageCLI, 'groups')
register_api(app, StageAPI, UsersClient, 'users')
register_api(app, TestAPI, None, '')
app.register_blueprint(data_retrieval, url_prefix='/data')
app.register_blueprint(logger)
