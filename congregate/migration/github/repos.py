import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes, safe_json_response, is_error_message_present
from congregate.migration.github.api.repos import ReposApi
from congregate.migration.github.users import UsersClient
from congregate.migration.github.api.users import UsersApi


class ReposClient(BaseClass):
    # Permissions placeholder
    GITHUB_PERMISSIONS_MAP = {
        ((u"admin", True), (u"push", True), (u"pull", True)): 40,  # Maintainer
        ((u"admin", False), (u"push", True), (u"pull", True)): 30,  # Developer
        ((u"admin", False), (u"push", False), (u"pull", True)): 20  # Reporter
    }

    GROUP_TYPE = ["Organization", "Enterprise"]

    def __init__(self):
        super(ReposClient, self).__init__()
        self.repos_api = ReposApi(
            self.config.source_host, self.config.source_token)
        self.users = UsersClient()
        self.users_api = UsersApi(
            self.config.source_host, self.config.source_token)

    def retrieve_repo_info(self):
        """
        List and transform all GitHub public repo to GitLab project metadata
        """
        projects = []
        self.format_repos(projects, self.repos_api.get_all_public_repos())
        with open('%s/data/project_json.json' % self.app_path, "w") as f:
            json.dump(remove_dupes(projects), f, indent=4)
        return remove_dupes(projects)

    def format_repos(self, projects, listed_repos, org=False):
        if projects is None:
            self.log.error("Failed to format repos {}".format(projects))
        else:
            for repo in listed_repos:
                projects.append({
                    "id": repo["id"],
                    "path": repo["name"],
                    "name": repo["name"],
                    "namespace": {
                        "id": repo["owner"]["id"],
                        "path": repo["owner"]["login"],
                        "name": repo["owner"]["login"],
                        "kind": "group" if repo["owner"]["type"] in self.GROUP_TYPE else "user",
                        "full_path": repo["owner"]["login"]
                    },
                    "path_with_namespace": repo["full_name"],
                    "visibility": "private" if repo["private"] else "public",
                    "description": repo.get("description", ""),
                    "members": self.add_members(repo["owner"]["type"], repo["owner"]["login"], repo["name"]) if not org else []
                })
        return projects

    def add_members(self, kind, owner, repo):
        """
        User repos have a single owner and collaborators (requires a collaborator PAT).
        Org and team repos have collaborators.
        """
        if kind in self.GROUP_TYPE:
            # org/team repo members are retrieved during staging
            members = []
            for c in self.repos_api.get_all_repo_collaborators(owner, repo):
                c["permissions"] = self.GITHUB_PERMISSIONS_MAP[tuple(
                    c.get("permissions", None).items())]
                members.append(c)
        elif kind == "User":
            members = [{"login": owner}]
            user_repo = safe_json_response(
                self.repos_api.get_repo(owner, repo))
            if not user_repo or is_error_message_present(user_repo):
                self.log.error("Failed to get JSON for user {} repo {} ({})".format(
                    owner, repo, user_repo))
                return []
            else:
                members[0]["permissions"] = self.GITHUB_PERMISSIONS_MAP[tuple(user_repo.get(
                    "permissions", None).items())]
        return self.users.format_users(members)
