from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import remove_dupes_but_take_higher_access, strip_netloc, safe_json_response
from gitlab_ps_utils.dict_utils import dig
from congregate.helpers.base_class import BaseClass
from congregate.helpers.utils import is_dot_com
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket import constants


class BitBucketServer(BaseClass):
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
        self.user_groups = {}
        self.repo_groups = {}
        self.project_groups = {}
        self.subset = subset
        self.skip_group_members = False
        self.skip_project_members = False
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
                "state": "active" if user["active"] else ("blocked" if is_dot_com else "deactivated"),
                # "is_admin": self.is_admin(user["slug"])
            }
        self.log.warning(
            f"User {user['slug']} is either not needed or missing the email address. Skipping")
        return None

    # def is_admin(self, user_slug):
    #     for user in self.users_api.get_user_permissions(user_slug):
    #         if user["user"]["slug"] == user_slug and user["permission"] in constants.BBS_ADMINS:
    #             return True
    #     return False

    def is_user_needed(self, user):
        return user.get("slug", "").lower() not in self.config.users_to_ignore

    def format_project(self, project, mongo):
        self.project_groups = {}
        return {
            "name": project["name"],
            "id": project["id"],
            "path": project["key"],
            "full_path": project["key"],
            # Always possible and safer than using 'public'
            "visibility": "private",
            "description": project.get("description", ""),
            "members": self.add_project_users([], project["key"]),
            "groups": self.project_groups,
            "projects": [] if self.subset else self.add_project_repos([], project["key"], mongo)
        }

    def add_project_users(self, users, project_key):
        for user in self.projects_api.get_all_project_users(project_key):
            u = user["user"]
            u["permission"] = constants.BBS_PROJECT_PERM_MAP[user["permission"]]
            users.append(u)

        if self.user_groups:
            users = self.add_project_user_groups(project_key, users)
        return remove_dupes_but_take_higher_access(
            self.format_users(users))

    def add_project_user_groups(self, project_key, users):
        for group in self.projects_api.get_all_project_groups(project_key):
            group_name = dig(group, 'group', 'name', default="").lower()
            permission = constants.BBS_PROJECT_PERM_MAP[group["permission"]]
            # Save project user groups in project "groups" field
            self.project_groups[group_name] = permission
            if not self.skip_group_members and self.user_groups.get(group_name):
                for user in self.user_groups[group_name]:
                    user["permission"] = permission
                    users.append(user)
            elif not self.skip_group_members:
                self.log.warning(
                    f"Unable to find project {project_key} user group {group_name} or the group is empty")
        return users

    def add_project_repos(self, repos, project_key, mongo):
        try:
            for repo in self.projects_api.get_all_project_repos(project_key):
                # Save all project repos ID references as part of group metadata
                repos.append(repo.get("id"))
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
        self.repo_groups = {}
        return {
            "id": repo["id"],
            "path": repo["slug"],
            "name": repo["name"],
            "archived": repo.get("archived", False),
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
            "groups": self.repo_groups,
            "default_branch": self.get_default_branch(repo_path, repo["slug"]),
            "http_url_to_repo": self.get_http_url_to_repo(repo)
        }

    def add_repo_users(self, users, project_key, repo_slug):
        for user in self.repos_api.get_all_repo_users(
                project_key, repo_slug):
            u = user["user"]
            u["permission"] = constants.BBS_REPO_PERM_MAP[user["permission"]]
            users.append(u)

        if self.user_groups:
            users = self.add_repo_user_groups(
                project_key, repo_slug, users)
        return remove_dupes_but_take_higher_access(
            self.format_users(users))

    def add_repo_user_groups(self, project_key, repo_slug, users):
        for group in self.repos_api.get_all_repo_groups(
                project_key, repo_slug):
            group_name = dig(group, 'group', 'name', default="").lower()
            permission = constants.BBS_REPO_PERM_MAP[group["permission"]]
            # Save repository user groups in repo "groups" field
            self.repo_groups[group_name] = permission
            if not self.skip_project_members and self.user_groups.get(group_name):
                for user in self.user_groups[group_name]:
                    user["permission"] = permission
                    users.append(user)
            elif not self.skip_project_members:
                self.log.warning(
                    f"Unable to find repo {repo_slug} user group {group_name} or the group is empty")
        return users

    def get_default_branch(self, project_key, repo_slug):
        resp = safe_json_response(
            self.repos_api.get_repo_default_branch(project_key, repo_slug))
        return resp.get("displayId", "master") if resp else "master"
