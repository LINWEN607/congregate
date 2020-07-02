import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket.users import UsersClient


class ReposClient(BaseClass):
    def __init__(self):
        self.repos_api = ReposApi()
        self.users_api = UsersApi()
        self.users = UsersClient()
        super(ReposClient, self).__init__()

    def retrieve_repo_info(self):
        # List and reformat all Bitbucket Server repo to GitLab project metadata
        repos = []
        for repo in self.repos_api.get_all_repos(
                self.config.external_source_url, self.config.external_user_token):
            repos.append({
                "id": repo["id"],
                "path": repo["slug"],
                "name": repo["name"],
                "namespace": {
                    "id": repo["project"]["id"],
                    "path": repo["project"]["key"],
                    "name": repo["project"]["name"],
                    "kind": "group",
                    "full_path": repo["project"]["key"],
                    "web_url": repo["project"]["links"]["self"][0]["href"]
                },
                "path_with_namespace": repo["project"]["key"] + "/" + repo["slug"],
                "visibility": "public" if repo["public"] else "private",
                "description": repo.get("description", ""),
                "members": self.add_members([], repo["project"]["key"], repo["slug"])
            })
        with open('%s/data/project_json.json' % self.app_path, "w") as f:
            json.dump(remove_dupes(repos), f, indent=4)
        return remove_dupes(repos)

    def add_members(self, members, project_key, repo_slug):
        bitbucket_permission_map = {
            "REPO_ADMIN": 40,  # Maintainer
            "REPO_WRITE": 30,  # Developer
            "REPO_READ": 20  # Reporter
        }
        for member in self.repos_api.get_all_repo_users(
                self.config.external_source_url, self.config.external_user_token, project_key, repo_slug):
            m = member["user"]
            m["permission"] = bitbucket_permission_map[member["permission"]]
            members.append(m)
        return self.users.format_users(members)
