import json

from urllib.parse import quote_plus
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes, remove_dupes_but_take_higher_access, safe_json_response, dig
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket.users import UsersClient
from congregate.migration.bitbucket.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi as GLProjectsApi


class ReposClient(BaseClass):
    def __init__(self):
        self.repos_api = ReposApi()
        self.users_api = UsersApi()
        self.users = UsersClient()
        self.groups_api = GroupsApi()
        self.gl_projects_api = GLProjectsApi()

        super(ReposClient, self).__init__()

    def retrieve_repo_info(self, groups=None):
        # List and reformat all Bitbucket Server repo to GitLab project metadata
        repos = []
        for repo in self.repos_api.get_all_repos():
            repo_path = dig(repo, 'project', 'key')
            repos.append({
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
                "path_with_namespace": repo_path + "/" + repo.get("slug"),
                "visibility": "public" if repo.get("public") else "private",
                "description": repo.get("description", ""),
                "members": self.add_repo_users([], repo_path, repo.get("slug"), groups),
                "default_branch": self.get_default_branch(repo_path, repo["slug"])
            })
        with open('%s/data/projects.json' % self.app_path, "w") as f:
            json.dump(remove_dupes(repos), f, indent=4)
        return remove_dupes(repos)

    def add_repo_users(self, members, project_key, repo_slug, groups):
        REPO_PERM_MAP = {
            "REPO_ADMIN": 40,  # Maintainer
            "REPO_WRITE": 30,  # Developer
            "REPO_READ": 20  # Reporter
        }
        for member in self.repos_api.get_all_repo_users(project_key, repo_slug):
            m = member["user"]
            m["permission"] = REPO_PERM_MAP[member["permission"]]
            members.append(m)

        if groups:
            for group in self.repos_api.get_all_repo_groups(project_key, repo_slug):
                group_name = dig(group, 'group', 'name', default="").lower()
                permission = REPO_PERM_MAP[group["permission"]]
                if groups.get(group_name, None):
                    for user in groups[group_name]:
                        temp_user = user
                        temp_user["permission"] = permission
                        members.append(temp_user)
                else:
                    self.log.warning(f"Unable to find group {group_name}")

        return remove_dupes_but_take_higher_access(self.users.format_users(members))

    def get_default_branch(self, project_key, repo_slug):
        resp = safe_json_response(
            self.repos_api.get_repo_default_branch(project_key, repo_slug))
        return resp.get("displayId", None) if resp else "master"

    def migrate_permissions(self, project, pid):
        perms = list(self.repos_api.get_repo_branch_permissions(
            project["namespace"], project["path"]))
        for p in perms:
            scope_type = dig(p, 'scope', 'type')
            if scope_type == "PROJECT":
                self.migrate_project_permissions(
                    p, [perm for perm in perms if dig(perm, 'scope', 'type') == "PROJECT"], pid)
            elif scope_type == "REPOSITORY":
                self.filter_branch_permissions(
                    p, [perm for perm in perms if dig(perm, 'scope', 'type') == "REPOSITORY"], pid)

    def migrate_project_permissions(self, p, perms, pid):
        # TODO: Should take precedence over project-level branch permissions
        self.log.warning(
            f"Skipping group level permission {p['type']} for branch {dig(p, 'matcher', 'displayId')} of project {pid}")

    def filter_branch_permissions(self, p, perms, pid):
        branch = dig(p, 'matcher', 'displayId', default="") 
        prio = ["read-only", "no-deletes",
                "fast-forward-only", "pull-request-only"]
        # Protect branch by highest priority and only once
        if any(perm["type"] == prio[0] for perm in perms if dig(perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(p, branch, pid) if p["type"] == prio[0] else None
        elif any(perm["type"] == prio[1] for perm in perms if dig(perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(p, branch, pid) if p["type"] == prio[1] else None
        elif any(perm["type"] == prio[2] for perm in perms if dig(perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(p, branch, pid) if p["type"] == prio[2] else None
        elif any(perm["type"] == prio[3] for perm in perms if dig(perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(p, branch, pid) if p["type"] == prio[3] else None

    def migrate_branch_permissions(self, p, branch, pid):
        """
            0  => No access
            30 => Developer access
            40 => Maintainer access
            50 => Admin access
        """
        # MODEL_BRANCH cannot be mapped
        PERM_MATCHER_TYPES = ["PATTERN", "BRANCH"]
        PERM_TYPES = {
            "read-only": [40, 40, 40],
            "no-deletes": [30, 30, 40],
            "fast-forward-only": [40, 30, 40],
            "pull-request-only": [30, 30, 40]
        }
        access_level = PERM_TYPES[p["type"]]
        data = {
            "name": branch if dig(p, 'matcher', 'type', 'id') in PERM_MATCHER_TYPES else None,
            "push_access_level": access_level[0],
            "merge_access_level": access_level[1],
            "unprotect_access_level": access_level[2]
        }

        if data["name"]:
            # Branch master is protected by default
            # if branch == "master":
            self.gl_projects_api.unprotect_repository_branches(
                pid, quote_plus(branch), self.config.destination_host, self.config.destination_token)
            status = self.gl_projects_api.protect_repository_branches(
                pid, branch, self.config.destination_host, self.config.destination_token, data=data).status_code
            if status != 201:
                self.log.error(
                    f"Failed to protect project {pid} branch {dig(p, 'matcher', 'displayId', default='')} with status: {status}")
        else:
            self.log.warning(
                f"Cannot match {dig(p, 'matcher', 'displayId', default='')} ({dig(p, 'matcher', 'type', 'id')}) for project {pid}")
        return data

    def correct_repo_description(self, src_repo, pid):
        self.log.info(
            f"Correcting project description for {src_repo['path_with_namespace']}")
        data = {
            "description": src_repo.get("description", "")
        }
        self.gl_projects_api.edit_project(
            self.config.destination_host, self.config.destination_token, pid, data=data)
