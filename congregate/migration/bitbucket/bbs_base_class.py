from gitlab_ps_utils.dict_utils import dig

from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector


class BBSBaseClass(BaseClass):
    @classmethod
    def connect_to_mongo(cls):
        return MongoConnector()

    @classmethod
    def format_project(cls, project):
        return {
            "name": project["name"],
            "id": project["id"],
            "path": project["key"],
            "full_path": project["key"],
            "visibility": "public" if project["public"] else "private",
            "description": project.get("description", ""),
            "members": [],
            "projects": []
        }

    @classmethod
    def format_repo(cls, repo, default_branch):
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
            "members": [],
            "default_branch": default_branch.get("displayId", "master") if default_branch else "master",
            "http_url_to_repo": cls.get_http_url_to_repo(repo)
        }

    @classmethod
    def get_http_url_to_repo(cls, repo):
        repo_clone_links = dig(repo, 'links', 'clone', default=[{"href": ""}])
        if repo_clone_links[0]["name"] == "http":
            return repo_clone_links[0]["href"]
        return repo_clone_links[1]["href"]

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
            }
        self.log.warning(
            f"User {user['slug']} is either not needed or missing the email address. Skipping")
        return None

    def is_user_needed(self, user):
        return user.get("slug", "").lower() not in self.config.users_to_ignore
