from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.helpers.migrate_utils import get_staged_projects
from congregate.helpers.misc_utils import get_dry_log, is_error_message_present


class BranchesClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        super().__init__()

    def set_default_branch(self, name=None, dry_run=True):
        for p in get_staged_projects():
            path = p.get("path_with_namespace")
            branch = name or p.get("default_branch", "master")
            self.log.info(
                f"{get_dry_log(dry_run)}Set project {path} default branch to {branch}")
            if not dry_run:
                self.set_branch(path, p.get("id"), branch)

    def set_branch(self, path, pid, branch):
        try:
            resp = self.projects_api.set_default_project_branch(
                pid,
                self.config.destination_host,
                self.config.destination_token,
                branch)
            is_error, _ = is_error_message_present(resp)
            if is_error or resp.status_code not in [200, 201]:
                self.log.error(
                    f"Failed to set project {path} default branch to {branch}, due to:\n{resp} - {resp.text}")
        except RequestException as e:
            self.log.error(
                f"Failed to set project {path} default branch to {branch}, with error:\n{e}")
