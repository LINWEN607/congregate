from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.helpers.misc_utils import get_dry_log


class BranchesClient(BaseClass):
    def __init__(self):
        self.users = UsersApi()
        self.groups = GroupsApi()
        self.projects = ProjectsApi()
        super(BranchesClient, self).__init__()

    def set_default_branches_to_master(self, dry_run=True):
        for project in self.projects.get_all_projects(self.config.destination_host, self.config.destination_token):
            if project.get("default_branch", None) == "master":
                path = project["path_with_namespace"]
                self.log.info("{0}Setting project {1} default branch to master".format(
                    get_dry_log(dry_run), path))
                if not dry_run:
                    try:
                        resp = self.projects.set_default_project_branch(
                            project["id"],
                            self.config.destination_host,
                            self.config.destination_token,
                            "master")
                        self.log.info(
                            "Project {0} default branch set to master ({1})".format(path, resp))
                    except RequestException, e:
                        self.log.error(
                            "Failed to set project {0} default branch to master, with error:\n{1}".format(path, e))
