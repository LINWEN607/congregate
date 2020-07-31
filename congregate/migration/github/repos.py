import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes
from congregate.migration.github.api.repos import ReposApi
from congregate.migration.github.users import UsersClient


class ReposClient(BaseClass):
    # Permissions placeholder
    GITHUB_PERMISSIONS_MAP = {
        ((u"admin", True), (u"push", True), (u"pull", True)): 40,  # Maintainer
        ((u"admin", False), (u"push", True), (u"pull", True)): 30,  # Developer
        ((u"admin", False), (u"push", False), (u"pull", True)): 20  # Reporter
    }

    def __init__(self):
        super(ReposClient, self).__init__()
        self.repos_api = ReposApi(
            self.config.source_host, self.config.source_token)
        self.users = UsersClient()

    def retrieve_repo_info(self):
        """
        List and transform all GitHub public repos to GitLab project metadata
        """
        repos = []
        self.format_repos(repos, self.repos_api.get_all_public_repos())
        with open('%s/data/project_json.json' % self.app_path, "w") as f:
            json.dump(remove_dupes(repos), f, indent=4)
        return remove_dupes(repos)

    def format_repos(self, repos, listed_repos):
        for repo in listed_repos:
            if repos is not None:
                repos.append({
                    "id": repo["id"],
                    "path": repo["name"],
                    "name": repo["name"],
                    "namespace": {
                        "id": repo["owner"]["id"],
                        "path": repo["owner"]["login"],
                        "name": repo["owner"]["login"],
                        "kind": "group" if repo["owner"]["type"] == "Organization" else "user",
                        "full_path": repo["owner"]["login"]
                    },
                    "path_with_namespace": repo["full_name"],
                    "visibility": "private" if repo["private"] else "public",
                    "description": repo.get("description", ""),
                    "members": []
                })
        return repos
