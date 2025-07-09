from gitlab_ps_utils.api import GitLabApi
from congregate.helpers.conf import Config
from congregate.helpers.utils import get_congregate_path

app_path = get_congregate_path()
log_name = 'congregate'
config = Config()
glapi = GitLabApi(app_path=app_path, log_name=log_name, ssl_verify=config.ssl_verify)
