import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.users import UsersClient
from congregate.migration.bitbucket.repos import ReposClient


class ProjectsClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.users = UsersClient()
        self.repos = ReposClient()
        super(ProjectsClient, self).__init__()

    def get_projects(self):
        with open("{}/data/groups.json".format(self.app_path), "r") as f:
            return json.load(f)

    def retrieve_project_info(self):
        obj = []
        projects = self.projects_api.get_all_projects(
            self.config.external_source_url, self.config.external_user_token)
        for project in projects:
            obj.append({
                "name": project["name"],
                "id": project["id"],
                "path": project["key"],
                "full_path": project["key"],
                "visibility": "public" if project["public"] else "private",
                "description": project.get("description", ""),
                "members": self.add_project_users([], project["key"]),
                "projects": self.add_project_repos([], project["key"]),
            })
        with open('%s/data/groups.json' % self.app_path, "w") as f:
            json.dump(remove_dupes(obj), f, indent=4)
        return remove_dupes(obj)

    def add_project_users(self, users, project_key):
        bitbucket_permission_map = {
            "PROJECT_ADMIN": 50,  # Owner
            "PROJECT_WRITE": 30,  # Developer
            "PROJECT_READ": 20  # Reporter
        }
        for user in self.projects_api.get_all_project_users(
                project_key, self.config.external_source_url, self.config.external_user_token):
            m = user["user"]
            m["permission"] = bitbucket_permission_map[user["permission"]]
            users.append(m)
        return self.users.format_users(users)

    def add_project_repos(self, repos, project_key):
        repos = []
        for repo in self.projects_api.get_all_project_repos(
                project_key, self.config.external_source_url, self.config.external_user_token):
            repos.append({
                "id": repo["id"],
                "path": repo["slug"],
                "name": repo["name"],
                "namespace": {
                    "id": repo["project"]["id"],
                    "name": repo["project"]["name"],
                    "path": repo["project"]["key"],
                    "kind": "group",
                    "full_path": repo["project"]["key"],
                    "web_url": repo["project"]["links"]["self"][0]["href"]
                },
                "path_with_namespace": repo["project"]["key"] + "/" + repo["slug"],
                "visibility": "public" if repo["public"] else "private",
                "description": repo.get("description", "")
            })
        return remove_dupes(repos)
