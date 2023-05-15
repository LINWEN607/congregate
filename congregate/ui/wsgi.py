from flask import Flask, render_template
from congregate.helpers import celery_utils
from congregate.cli.stage_projects import ProjectStageCLI
from congregate.cli.stage_groups import GroupStageCLI
from congregate.migration.gitlab.users import UsersClient
from congregate.ui.stage import StageAPI
from congregate.ui.models import data_retrieval
from congregate.ui.logs import logger
from congregate.ui.airgap import airgap_routes

app = Flask(__name__,
            static_folder = "../../dist/assets",
            template_folder = "../../dist")

app.config.from_mapping(
    CELERY=celery_utils.generate_celery_config()
)

celery_app = celery_utils.celery_init_app(app)

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
app.register_blueprint(data_retrieval, url_prefix='/data')
app.register_blueprint(logger)
app.register_blueprint(airgap_routes, url_prefix='/airgap')
