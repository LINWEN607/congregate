from os import getenv
from flask import Flask, render_template
from flask_cors import CORS
from congregate.helpers import celery_utils
from congregate.cli.stage_projects import ProjectStageCLI
from congregate.cli.stage_groups import GroupStageCLI
from congregate.cli.stage_users import UserStageCLI
from congregate.ui.stage import StageAPI
from congregate.ui.list import list_functions
from congregate.ui.models import data_retrieval
from congregate.ui.logs import logger
from congregate.ui.airgap import airgap_routes
from congregate.ui.direct_transfer import direct_transfer_routes
from congregate.ui.jobs import job_queue_routes
from congregate.ui import config
from congregate.ui.settings import settings

app = Flask(__name__,
            static_folder = "../../dist/assets",
            template_folder = "../../dist")

app.config.from_mapping(
    CELERY=celery_utils.generate_celery_config(),
    UPLOAD_FOLDER=config.filesystem_path
)

# TODO: add check for development mode to enable cors
if int(getenv('FLASK_DEBUG', 0)) == 1:
    CORS(app, resources={r"/api/*": {"origins": "*"}})

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
register_api(app, StageAPI, UserStageCLI, 'users')
app.register_blueprint(data_retrieval, url_prefix='/api/data')
app.register_blueprint(logger)
app.register_blueprint(settings, url_prefix='/api')
app.register_blueprint(list_functions, url_prefix='/api')
app.register_blueprint(job_queue_routes, url_prefix='/api/jobs')
if config.airgap:
    app.register_blueprint(airgap_routes, url_prefix='/api/airgap')
if config.direct_transfer:
    app.register_blueprint(direct_transfer_routes, url_prefix='/api/direct_transfer')
