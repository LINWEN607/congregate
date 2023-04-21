import subprocess
from flask import Flask, render_template, Response, stream_with_context
from congregate.helpers.utils import get_congregate_path
from congregate.cli.stage_projects import ProjectStageCLI
from congregate.cli.stage_groups import GroupStageCLI
from congregate.migration.gitlab.users import UsersClient
from congregate.ui.stage import StageAPI
from congregate.ui.test import TestAPI
from congregate.ui.models import data_retrieval

app = Flask(__name__,
            static_folder = "../../dist/assets",
            template_folder = "../../dist")

@app.route("/")
@app.route("/home")
def home_page():
    return render_template("index.html")

@app.route('/log')
def generate_stream():
    def generate():
        last_line = ""
        while True:
            output = subprocess.check_output(
                ['tail', '-n 1', f'{get_congregate_path()}/data/logs/congregate.log'])
            if output == last_line:
                yield ""
            else:
                last_line = output
                yield "<p>" + output.split("|")[-1] + "</p>"
            subprocess.call(['sleep', '1'])

    return Response(stream_with_context(generate()))

@app.route('/logLine')
def return_last_line():
    output = subprocess.check_output(
        ['tail', '-n 1', f'{get_congregate_path()}/data/logs/congregate.log'])
    return output.split(":")[-1]

def register_api(app, api, client, name):
    asset = api.as_view(f"{name}", client, name)
    app.add_url_rule(f"/api/{api.route_prefix}/{name}/", view_func=asset)

register_api(app, StageAPI, ProjectStageCLI, 'projects')
register_api(app, StageAPI, GroupStageCLI, 'groups')
register_api(app, StageAPI, UsersClient, 'users')
register_api(app, TestAPI, None, '')
app.register_blueprint(data_retrieval, url_prefix='/data')