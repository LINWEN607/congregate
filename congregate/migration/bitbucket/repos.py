import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes, remove_dupes_but_take_higher_access
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket.users import UsersClient
from congregate.migration.bitbucket.api.groups import GroupsApi


class ReposClient(BaseClass):
    def __init__(self):
        self.repos_api = ReposApi()
        self.users_api = UsersApi()
        self.users = UsersClient()
        self.groups_api = GroupsApi()
        super(ReposClient, self).__init__()

    def retrieve_repo_info(self, groups=None):
        # List and reformat all Bitbucket Server repo to GitLab project metadata
        repos = []
        for repo in self.repos_api.get_all_repos(
                self.config.source_host):
            repos.append({
                "id": repo["id"],
                "path": repo["slug"],
                "name": repo["name"],
                "namespace": {
                    "id": repo["project"]["id"],
                    "path": repo["project"]["key"],
                    "name": repo["project"]["name"],
                    "kind": "group",
                    "full_path": repo["project"]["key"]
                },
                "path_with_namespace": repo["project"]["key"] + "/" + repo["slug"],
                "visibility": "public" if repo["public"] else "private",
                "description": repo.get("description", ""),
                "members": self.add_repo_users([], repo["project"]["key"], repo["slug"], groups)
            })
        with open('%s/data/project_json.json' % self.app_path, "w") as f:
            json.dump(remove_dupes(repos), f, indent=4)
        return remove_dupes(repos)

    def add_repo_users(self, members, project_key, repo_slug, groups):
        bitbucket_permission_map = {
            "REPO_ADMIN": 40,  # Maintainer
            "REPO_WRITE": 30,  # Developer
            "REPO_READ": 20  # Reporter
        }
        for member in self.repos_api.get_all_repo_users(
                self.config.source_host, project_key, repo_slug):
            m = member["user"]
            m["permission"] = bitbucket_permission_map[member["permission"]]
            members.append(m)

        if groups:
            for group in self.repos_api.get_all_repo_groups(self.config.source_host, project_key, repo_slug):
                group_name = group["group"]["name"].lower()
                permission = bitbucket_permission_map[group["permission"]]
                if groups.get(group_name, None):
                    for user in groups[group_name]:
                        temp_user = user
                        temp_user["permission"] = permission
                        members.append(temp_user)
                else:
                    self.log.warning(f"Unable to find group {group_name}")
        
        return remove_dupes_but_take_higher_access(self.users.format_users(members))
