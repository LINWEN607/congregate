from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import remove_dupes_but_take_higher_access, strip_netloc, safe_json_response
from gitlab_ps_utils.dict_utils import dig
from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.migration.bitbucket.api.users import UsersApi


class BitBucketServer(BaseClass):
    @classmethod
    def connect_to_mongo(cls):
        return MongoConnector()

    @classmethod
    def get_http_url_to_repo(cls, repo):
        repo_clone_links = dig(repo, 'links', 'clone', default=[{"href": ""}])
        if repo_clone_links[0]["name"] == "http":
            return repo_clone_links[0]["href"]
        return repo_clone_links[1]["href"]

    def __init__(self, subset=False):
        self.projects_api = ProjectsApi()
        self.repos_api = ReposApi()
        self.users_api = UsersApi()
        self.user_groups = None
        self.subset = subset
        self.ADMINS = ["SYS_ADMIN", "ADMIN"]
        super().__init__()

    def format_users(self, users):
        data = []
        for user in users:
            formatted_user = self.format_user(user)
            if not formatted_user:
                continue
            if user.get("permission"):
                formatted_user["access_level"] = user["permission"]
            data.append(formatted_user)
        return data

    def format_user(self, user):
        if self.is_user_needed(user) and user.get("emailAddress"):
            return {
                "id": user["id"],
                "username": user["slug"],
                "name": user["displayName"],
                "email": user["emailAddress"].lower(),
                "state": "active"
                # "is_admin": self.is_admin(user["slug"])
            }
        self.log.warning(
            f"User {user['slug']} is either not needed or missing the email address. Skipping")
        return None

    # def is_admin(self, user_slug):
    #     for user in self.users_api.get_user_permissions(user_slug):
    #         if user["user"]["slug"] == user_slug and user["permission"] in self.ADMINS:
    #             return True
    #     return False

    def is_user_needed(self, user):
        return user.get("slug", "").lower() not in self.config.users_to_ignore

    def format_project(self, project, mongo):
        return {
            "name": project["name"],
            "id": project["id"],
            "path": project["key"],
            "full_path": project["key"],
            "visibility": "public" if project["public"] else "private",
            "description": project.get("description", ""),
            "members": self.add_project_users([], project["key"], self.user_groups),
            "projects": self.add_project_repos([], project["key"], mongo)
        }

    def add_project_users(self, users, project_key, groups):
        bitbucket_permission_map = {
            "PROJECT_ADMIN": 50,  # Owner
            "PROJECT_WRITE": 30,  # Developer
            "PROJECT_READ": 20  # Reporter
        }
        for user in self.projects_api.get_all_project_users(project_key):
            m = user["user"]
            m["permission"] = bitbucket_permission_map[user["permission"]]
            users.append(m)

        if groups:
            for group in self.projects_api.get_all_project_groups(project_key):
                group_name = dig(group, 'group', 'name', default="").lower()
                permission = bitbucket_permission_map[group["permission"]]
                if groups.get(group_name):
                    for user in groups[group_name]:
                        temp_user = user
                        temp_user["permission"] = permission
                        users.append(temp_user)
                else:
                    self.log.warning(
                        f"Unable to find project {project_key} user group {group_name} or the group is empty")

        return remove_dupes_but_take_higher_access(
            self.format_users(users))

    def add_project_repos(self, repos, project_key, mongo):
        try:
            for repo in self.projects_api.get_all_project_repos(project_key):
                # Save all project repos ID references as part of group metadata
                repos.append(repo.get("id"))
                # List BB Server project repos
                if self.subset:
                    mongo.insert_data(
                        f"projects-{strip_netloc(self.config.source_host)}",
                        self.format_repo(repo))
            # Remove duplicate entries
            return list(set(repos))
        except RequestException as re:
            self.log.error(
                f"Failed to GET repos from project '{project_key}', with error:\n{re}")
            return None

    def format_repo(self, repo, project=False):
        """
        Format public and project repos.
        Leave project repo members empty ([]) as they are retrieved during staging.
        """
        repo_path = dig(repo, 'project', 'key')
        return {
            "id": repo["id"],
            "path": repo["slug"],
            "name": repo["name"],
            "namespace": {
                "id": dig(repo, 'project', 'id'),
                "path": repo_path,
                "name": dig(repo, 'project', 'name'),
                "kind": "group",
                "full_path": dig(repo, 'project', 'key')
            },
            "path_with_namespace": f"{repo_path}/{repo.get('slug')}",
            "visibility": "public" if repo.get("public") else "private",
            "description": repo.get("description", ""),
            "members": [] if project else self.add_repo_users([], repo_path, repo.get("slug")),
            "default_branch": self.get_default_branch(repo_path, repo["slug"]),
            "http_url_to_repo": self.get_http_url_to_repo(repo)
        }

    def add_repo_users(self, members, project_key, repo_slug):
        REPO_PERM_MAP = {
            "REPO_ADMIN": 40,  # Maintainer
            "REPO_WRITE": 30,  # Developer
            "REPO_READ": 20  # Reporter
        }
        for member in self.repos_api.get_all_repo_users(
                project_key, repo_slug):
            m = member["user"]
            m["permission"] = REPO_PERM_MAP[member["permission"]]
            members.append(m)

        if self.user_groups:
            for group in self.repos_api.get_all_repo_groups(
                    project_key, repo_slug):
                group_name = dig(group, 'group', 'name', default="").lower()
                permission = REPO_PERM_MAP[group["permission"]]
                if self.user_groups.get(group_name):
                    for user in self.user_groups[group_name]:
                        temp_user = user
                        temp_user["permission"] = permission
                        members.append(temp_user)
                else:
                    self.log.warning(
                        f"Unable to find repo {repo_slug} user group {group_name} or the group is empty")

        return remove_dupes_but_take_higher_access(
            self.format_users(members))

    def get_default_branch(self, project_key, repo_slug):
        resp = safe_json_response(
            self.repos_api.get_repo_default_branch(project_key, repo_slug))
        return resp.get("displayId", "master") if resp else "master"
