from time import time
from urllib.parse import quote_plus
from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import get_dry_log, safe_json_response, remove_dupes_but_take_higher_access, strip_netloc, is_error_message_present
from gitlab_ps_utils.dict_utils import dig
from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.migrate_utils import get_subset_list, check_list_subset_input_file_path
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket.users import UsersClient
from congregate.migration.bitbucket.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi as GLProjectsApi
from congregate.helpers.migrate_utils import get_staged_projects, add_post_migration_stats, get_staged_groups
from congregate.helpers.utils import rotate_logs


class ReposClient(BaseClass):
    @classmethod
    def connect_to_mongo(cls):
        return MongoConnector()

    @classmethod
    def format_repo_parent_project(cls, project):
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
    def get_http_url_to_repo(cls, repo):
        repo_clone_links = dig(repo, 'links', 'clone', default=[{"href": ""}])
        if repo_clone_links[0]["name"] == "http":
            return repo_clone_links[0]["href"]
        return repo_clone_links[1]["href"]

    def __init__(self, subset=False):
        self.projects_api = ProjectsApi()
        self.repos_api = ReposApi()
        self.users_api = UsersApi()
        self.users = UsersClient()
        self.groups_api = GroupsApi()
        self.gl_projects_api = GLProjectsApi()
        self.user_groups = None
        self.subset = subset
        self.unique_projects = set()
        super().__init__()

    def set_user_groups(self, groups):
        self.user_groups = groups

    def retrieve_repo_info(self, processes=None):
        if self.subset:
            subset_path = check_list_subset_input_file_path()
            self.log.info(
                f"Listing subset of {self.config.source_host} repos from '{subset_path}'")
            self.multi.start_multi_process_stream_with_args(
                self.handle_repos_subset, get_subset_list(), processes=processes, nestable=True)
        else:
            self.multi.start_multi_process_stream_with_args(
                self.handle_retrieving_repos, self.repos_api.get_all_repos(), processes=processes, nestable=True)

    def handle_repos_subset(self, repo):
        # e.g. https://www.bitbucketserverexample.com/scm/test_project/repos/test_repo.git"
        repo_split = repo.split("/")
        project_key = repo_split[4]
        repo_slug = repo_split[-1].rstrip(".git")
        try:
            self.log.info(
                f"Listing project '{project_key}' repo '{repo_slug}'")
            repo_json = self.repos_api.get_repo(project_key, repo_slug)
            self.handle_retrieving_repos(repo_json, project_key=project_key)
        except RequestException as re:
            self.log.error(
                f"Failed to GET project '{project_key}' repo '{repo_slug}', with error:\n{re}")

    def handle_retrieving_repos(self, repo, mongo=None, project_key=None):
        # List and reformat all Bitbucket Server repo to GitLab project metadata
        error, resp = is_error_message_present(repo)
        if resp and not error:
            if project_key and project_key not in self.unique_projects:
                self.handle_retrieving_repo_parent_project(
                    resp.get("slug"), project_key)

            # mongo should be set to None unless this function is being used in a unit test
            if not mongo:
                mongo = self.connect_to_mongo()
            mongo.insert_data(
                f"projects-{strip_netloc(self.config.source_host)}",
                self.format_repo(resp))
            mongo.close_connection()
        else:
            self.log.error(resp)

    def handle_retrieving_repo_parent_project(self, repo_slug, project_key, mongo=None):
        if project := self.list_repo_parent_project(repo_slug, project_key):
            # mongo should be set to None unless this function is being used in a unit test
            if not mongo:
                mongo = self.connect_to_mongo()
            mongo.insert_data(
                f"groups-{strip_netloc(self.config.source_host)}",
                self.format_repo_parent_project(project))
            mongo.close_connection()

    def list_repo_parent_project(self, repo_slug, project_key):
        try:
            self.log.info(
                f"Listing repo '{repo_slug}' parent project '{project_key}'")
            project_json = self.projects_api.get_project(project_key)
            error, resp = is_error_message_present(project_json)
            if resp and not error:
                self.unique_projects.add(project_key)
                return resp
            self.log.error(resp)
            return None
        except RequestException as re:
            self.log.error(
                f"Failed to GET repo '{repo_slug}' parent project '{project_key}', with error:\n{re}")
            return None

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
            self.users.format_users(members))

    def get_default_branch(self, project_key, repo_slug):
        resp = safe_json_response(
            self.repos_api.get_repo_default_branch(project_key, repo_slug))
        return resp.get("displayId", "master") if resp else "master"

    def migrate_permissions(self, project, pid):
        perms = list(self.repos_api.get_all_repo_branch_permissions(
            project["namespace"], project["path"]))
        for p in perms:
            scope_type = dig(p, 'scope', 'type')
            if scope_type == "PROJECT":
                # Too granular to map to GL group default_branch_protection
                self.log.warning(
                    f"Skipping group level permission {p['type']} for branch {dig(p, 'matcher', 'displayId')} of project {pid}")
            elif scope_type == "REPOSITORY":
                self.filter_branch_permissions(
                    p, [perm for perm in perms if dig(perm, 'scope', 'type') == "REPOSITORY"], pid)

    def filter_branch_permissions(self, p, perms, pid):
        branch = dig(p, 'matcher', 'displayId', default="")
        prio = ["read-only", "no-deletes",
                "fast-forward-only", "pull-request-only"]
        # Protect branch by highest priority and only once
        if any(perm["type"] == prio[0] for perm in perms if dig(
                perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(
                p, branch, pid) if p["type"] == prio[0] else None
        elif any(perm["type"] == prio[1] for perm in perms if dig(perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(
                p, branch, pid) if p["type"] == prio[1] else None
        elif any(perm["type"] == prio[2] for perm in perms if dig(perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(
                p, branch, pid) if p["type"] == prio[2] else None
        elif any(perm["type"] == prio[3] for perm in perms if dig(perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(
                p, branch, pid) if p["type"] == prio[3] else None

    def migrate_branch_permissions(self, p, branch, pid):
        """
        Map BB permissions to GL roles, skip BB user and group restriction exceptions
        GL access level mapping:
            0  => No access
            30 => Developer access
            40 => Maintainer access
            60 => Admin access
        """
        # MODEL_BRANCH cannot be mapped
        PERM_MATCHER_TYPES = ["PATTERN", "BRANCH"]
        PERM_TYPES = {
            "read-only": [40, 40, 40],
            "no-deletes": [30, 30, 40],
            "fast-forward-only": [40, 30, 40],
            "pull-request-only": [30, 30, 40]
        }
        access_levels = PERM_TYPES[p["type"]]
        data = {
            "name": branch if dig(p, 'matcher', 'type', 'id') in PERM_MATCHER_TYPES else None,
            "push_access_level": access_levels[0],
            "merge_access_level": access_levels[1],
            "unprotect_access_level": access_levels[2]
        }

        if data["name"]:
            # Branch master/main is protected by default
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

    def update_branch_permissions(self, restrict=True, is_project=False, dry_run=True):
        start = time()
        rotate_logs()
        staged = get_staged_groups() if is_project else get_staged_projects()
        object_type = "project" if is_project else "repo"
        self.log.info(f"BitBucket {object_type} count: {len(staged)}")
        try:
            for s in staged:
                s_path = s.get("path") if is_project else s.get(
                    "path_with_namespace")
                self.log.info(
                    f"{get_dry_log(dry_run)}{'Add' if restrict else 'Remove'} BitBucket {object_type} '{s_path}' branch permissions")
                if not dry_run:
                    self.add_branch_permissions(
                        s, s_path, is_project) if restrict else self.remove_branch_permissions(s, s_path, is_project)
        except RequestException as re:
            self.log.error(
                f"Failed to {'add' if restrict else 'remove'} BitBucket {object_type} '{s_path}' branch permissions, with error:\n{re}")
        finally:
            add_post_migration_stats(start, log=self.log)

    def add_branch_permissions(self, staged, s_path, is_project):
        matcher = {
            "id": "*",
            "type": {
                "id": "PATTERN",
                "name": "Pattern"
            }
        }
        data = [
            {
                "type": "fast-forward-only",
                "matcher": matcher
            },
            {
                "type": "no-deletes",
                "matcher": matcher
            },
            {
                "type": "pull-request-only",
                "matcher": matcher
            },
            {
                "type": "read-only",
                "matcher": matcher
            }
        ]
        if is_project:
            resp = self.projects_api.create_project_branch_permissions(
                staged["path"], data=data)
        else:
            resp = self.repos_api.create_repo_branch_permissions(
                staged["namespace"], staged["path"], data=data)
        if resp.status_code != 200:
            self.log.error(
                f"Failed to add {'project' if is_project else 'repo'} '{s_path}' branch permissions:\n{resp} - {resp.text}")

    def remove_branch_permissions(self, staged, s_path, is_project):
        if is_project:
            restrictions = self.projects_api.get_all_project_branch_permissions(
                staged["path"])
        else:
            restrictions = self.repos_api.get_all_repo_branch_permissions(
                staged["namespace"], staged["path"])
        for r in restrictions:
            # Remove all wildcard (*) branch permissions
            if r.get("matcher") and r["matcher"].get("id") == "*":
                if is_project:
                    resp = self.projects_api.delete_project_branch_permission(
                        staged["path"], r["id"])
                else:
                    resp = self.repos_api.delete_repo_branch_permission(
                        staged["namespace"], staged["path"], r["id"])
            if resp.status_code != 204:
                self.log.error(
                    f"Failed to remove {'project' if is_project else 'repo'} '{s_path}' branch permission:\n{r}\n{resp} - {resp.text}")
