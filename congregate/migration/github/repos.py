import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes
from congregate.migration.github.api.repos import ReposApi


class ReposClient(BaseClass):
    def __init__(self):
        super(ReposClient, self).__init__()
        self.repos_api = ReposApi(
            self.config.source_host, self.config.source_token)

    def retrieve_repo_info(self):
        repos = self.repos_api.get_all_public_repos()
        with open("{}/data/project_json.json".format(self.app_path), "w") as f:
            json.dump(remove_dupes(repos), f, indent=4)
        return remove_dupes(repos)
