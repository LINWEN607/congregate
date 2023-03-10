from time import time
from urllib.parse import quote_plus
from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import get_dry_log, strip_netloc, is_error_message_present
from gitlab_ps_utils.dict_utils import dig
from congregate.helpers.migrate_utils import get_subset_list, check_list_subset_input_file_path
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.migration.gitlab.api.projects import ProjectsApi as GLProjectsApi
from congregate.helpers.migrate_utils import get_staged_projects, add_post_migration_stats, get_staged_groups
from congregate.helpers.utils import rotate_logs
from congregate.migration.bitbucket.base import BitBucketServer
from congregate.migration.bitbucket import constants
from congregate.helpers.mdbc import MongoConnector


class ReposClient(BitBucketServer):
    def __init__(self, subset=False, skip_project_members=False, skip_group_members=False):
        self.projects_api = ProjectsApi()
        self.repos_api = ReposApi()
        self.gl_projects_api = GLProjectsApi()
        self.unique_projects = set()
        super().__init__()
        self.subset = subset
        self.skip_project_members = skip_project_members
        self.skip_group_members = skip_group_members

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
        repo_slug = repo_split[-1].replace(".git", "")
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
                mongo = MongoConnector()
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
                mongo = MongoConnector()
            mongo.insert_data(
                f"groups-{strip_netloc(self.config.source_host)}",
                self.format_project(project, mongo))
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
        pri = ["read-only", "pull-request-only",
               "no-deletes", "fast-forward-only"]
        # Protect branch by highest priority and only once
        if any(perm["type"] == pri[0] for perm in perms if dig(
                perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(
                p, branch, pid) if p["type"] == pri[0] else None
        if any(perm["type"] == pri[1] for perm in perms if dig(perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(
                p, branch, pid) if p["type"] == pri[1] else None
        if any(perm["type"] == pri[2] for perm in perms if dig(perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(
                p, branch, pid) if p["type"] == pri[2] else None
        if any(perm["type"] == pri[3] for perm in perms if dig(perm, 'matcher', 'displayId') == branch):
            return self.migrate_branch_permissions(
                p, branch, pid) if p["type"] == pri[3] else None
        return None

    def migrate_branch_permissions(self, p, branch, pid):
        """
        Map BB permissions to GL (core/free) roles, skip BB user and group restriction exceptions
        GL access level mapping:
            0  => No access
            30 => Developer access
            40 => Maintainer access
            60 => Admin access
        """
        # MODEL_BRANCH cannot be mapped
        PERM_MATCHER_TYPES = ["PATTERN", "BRANCH"]
        PERM_TYPES = {
            "read-only": [0, 0, 40],
            "pull-request-only": [0, 40, 40],
            "no-deletes": [40, 40, 40],
            "fast-forward-only": [40, 40, 40]
        }
        access_levels = PERM_TYPES[p["type"]]
        data = {
            "name": branch if dig(p, 'matcher', 'type', 'id') in PERM_MATCHER_TYPES else None,
            "push_access_level": access_levels[0],      # GitLab default - 40
            "merge_access_level": access_levels[1],     # GitLab default - 40
            "unprotect_access_level": access_levels[2]  # GitLab default - 40
        }

        if data["name"]:
            # Branch master/main is protected by default
            self.gl_projects_api.unprotect_repository_branches(
                pid, quote_plus(branch), self.config.destination_host, self.config.destination_token)
            status = self.gl_projects_api.protect_repository_branches(
                pid, branch, self.config.destination_host, self.config.destination_token, data=data).status_code
            if status != 201:
                self.log.error(
                    f"Failed to protect project {pid} branch {branch}, with status: {status}")
        else:
            self.log.warning(f"Cannot match project {pid} branch {branch}")
        return data

    def correct_repo_description(self, src_repo, pid):
        self.log.info(
            f"Correcting project description for {src_repo['path_with_namespace']}")
        data = {
            "description": src_repo.get("description", "")
        }
        self.gl_projects_api.edit_project(
            self.config.destination_host, self.config.destination_token, pid, data=data)

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

    def update_member_permissions(self, restrict=True, is_project=False, dry_run=True):
        start = time()
        rotate_logs()
        staged = get_staged_groups() if is_project else get_staged_projects()
        object_type = "project" if is_project else "repo"
        self.log.info(f"BitBucket {object_type} count: {len(staged)}")
        self.log.warning(
            "Make sure to '--skip-group-members' and '--skip-project-members' when listing, to avoid including user groups into repo and project 'members'")
        try:
            for s in staged:
                s_path = s.get("path") if is_project else s.get(
                    "path_with_namespace")
                self.log.info(
                    f"{get_dry_log(dry_run)}{'Set' if restrict else 'Unset'} BitBucket {object_type} '{s_path}' read-only member permissions")
                if not dry_run:
                    self.handle_member_permissions(
                        s, s_path, restrict, is_project)
        except RequestException as re:
            self.log.error(
                f"Failed to {'set' if restrict else 'unset'} BitBucket {object_type} '{s_path}' read-only member permissions, with error:\n{re}")
        finally:
            add_post_migration_stats(start, log=self.log)

    def handle_member_permissions(self, staged, s_path, restrict, is_project):
        if is_project:
            if restrict:
                self.set_project_member_permissions(staged, s_path)
            else:
                self.unset_project_member_permissions(staged, s_path)
        else:
            if restrict:
                self.set_repo_member_permissions(staged, s_path)
            else:
                self.unset_repo_member_permissions(staged, s_path)

    def set_project_member_permissions(self, staged, s_path):
        permission = "PROJECT_READ"
        access_level = constants.BBS_PROJECT_PERM_MAP[permission]
        self.set_project_member_user_permissions(
            staged, s_path, permission, access_level)
        self.set_project_member_group_permissions(
            staged, s_path, permission, access_level)

    def set_project_member_user_permissions(self, staged, s_path, permission, access_level):
        # Set permission for all project users in bulk
        users = ""
        for u in staged.get("members", []):
            if u["access_level"] > access_level:
                users += f"&name={u['username']}" if users else f"name={u['username']}"
        if users:
            users += f"&permission={permission}"
            resp = self.projects_api.set_project_user_permissions(
                s_path, data=users)
            if resp.status_code != 204:
                self.log.error(
                    f"Failed to set project '{s_path}' '{permission}' permission for all users:\n{resp} - {resp.text}")

    def set_project_member_group_permissions(self, staged, s_path, permission, access_level):
        # Set permission for all project groups in bulk
        groups = ""
        for k, v in staged.get("groups", {}).items():
            if v > access_level:
                groups += f"&name={k}" if groups else f"name={k}"
        if groups:
            groups += f"&permission={permission}"
            resp = self.projects_api.set_project_group_permissions(
                s_path, data=groups)
            if resp.status_code != 204:
                self.log.error(
                    f"Failed to set project '{s_path}' '{permission}' permission for all groups:\n{resp} - {resp.text}")

    def set_repo_member_permissions(self, staged, s_path):
        permission = "REPO_READ"
        access_level = constants.BBS_REPO_PERM_MAP[permission]
        paths = s_path.split("/")
        project_key, repo_slug = paths[0], paths[1]
        self.set_repo_member_user_permissions(
            staged, project_key, repo_slug, permission, access_level)
        self.set_repo_member_group_permissions(
            staged, project_key, repo_slug, permission, access_level)

    def set_repo_member_user_permissions(self, staged, project_key, repo_slug, permission, access_level):
        # Set permission for all repo users in bulk
        users = ""
        for u in staged.get("members", []):
            if u["access_level"] > access_level:
                users += f"&name={u['username']}" if users else f"name={u['username']}"
        if users:
            users += f"&permission={permission}"
            resp = self.repos_api.set_repo_user_permissions(
                project_key, repo_slug, data=users)
            if resp.status_code != 204:
                self.log.error(
                    f"Failed to set repo '{project_key}/{repo_slug}' '{permission}' permission for all users:\n{resp} - {resp.text}")

    def set_repo_member_group_permissions(self, staged, project_key, repo_slug, permission, access_level):
        # Set permission for all repo groups in bulk
        groups = ""
        for k, v in staged.get("groups", {}).items():
            if v > access_level:
                groups += f"&name={k}" if groups else f"name={k}"
        if groups:
            groups += f"&permission={permission}"
            resp = self.repos_api.set_repo_group_permissions(
                project_key, repo_slug, data=groups)
            if resp.status_code != 204:
                self.log.error(
                    f"Failed to set repo '{project_key}/{repo_slug}' '{permission}' permission for all groups:\n{resp} - {resp.text}")

    def unset_project_member_permissions(self, staged, s_path):
        access_level = 20
        self.unset_project_member_user_permissions(
            staged, s_path, access_level)
        self.unset_project_member_group_permissions(
            staged, s_path, access_level)

    def unset_project_member_user_permissions(self, staged, s_path, access_level):
        # Handle individual project users
        for u in staged.get("members", []):
            if u["access_level"] > access_level:
                permission = constants.GL_GROUP_PERM_MAP[u['access_level']]
                data = f"name={u['username']}&permission={permission}"
                resp = self.projects_api.set_project_user_permissions(
                    s_path, data=data)
                if resp.status_code != 204:
                    self.log.error(
                        f"Failed to set project '{s_path}' '{permission}' permission for all users:\n{resp} - {resp.text}")

    def unset_project_member_group_permissions(self, staged, s_path, access_level):
        # Handle individual project groups
        for k, v in staged.get("groups", {}).items():
            if v > access_level:
                permission = constants.GL_GROUP_PERM_MAP[v]
                data = f"name={k}&permission={permission}"
                resp = self.projects_api.set_project_group_permissions(
                    s_path, data=data)
                if resp.status_code != 204:
                    self.log.error(
                        f"Failed to set project '{s_path}' '{permission}' permission for all groups:\n{resp} - {resp.text}")

    def unset_repo_member_permissions(self, staged, s_path):
        access_level = 20
        paths = s_path.split("/")
        project_key, repo_slug = paths[0], paths[1]
        self.unset_repo_member_user_permissions(
            staged, project_key, repo_slug, access_level)
        self.unset_repo_member_group_permissions(
            staged, project_key, repo_slug, access_level)

    def unset_repo_member_user_permissions(self, staged, project_key, repo_slug, access_level):
        # Handle individual repo users
        for u in staged.get("members", []):
            if u["access_level"] > access_level:
                permission = constants.GL_PROJECT_PERM_MAP[u['access_level']]
                data = f"name={u['username']}&permission={permission}"
                resp = self.repos_api.set_repo_user_permissions(
                    project_key, repo_slug, data=data)
                if resp.status_code != 204:
                    self.log.error(
                        f"Failed to set repo '{project_key}/{repo_slug}' '{permission}' permission for all users:\n{resp} - {resp.text}")

    def unset_repo_member_group_permissions(self, staged, project_key, repo_slug, access_level):
        # Handle individual repo groups
        for k, v in staged.get("groups", {}).items():
            if v > access_level:
                permission = constants.GL_PROJECT_PERM_MAP[v]
                data = f"name={k}&permission={permission}"
                resp = self.repos_api.set_repo_group_permissions(
                    project_key, repo_slug, data=data)
                if resp.status_code != 204:
                    self.log.error(
                        f"Failed to set repo '{project_key}/{repo_slug}' '{permission}' permission for all groups:\n{resp} - {resp.text}")

    def transform_pull_requests(self, pull_requests):
        return [{
            "title": pr["title"],
            "state": constants.PR_STATE_MAPPING.get(pr["state"]),
            "author": {
                "username": dig(pr, "author", "user", "slug"),
            }
        } for pr in pull_requests]

    def transform_branches(self, branches):
        return [{
            "name": b["displayId"],
            "commit": {
                "id": b["latestCommit"],
            },
            "default": b["isDefault"]
        } for b in branches]

    def transform_tags(self, tags):
        return [{
            "name": t["displayId"],
            "commit": {
                "id": t["latestCommit"],
            },
            "target": t["hash"]
        } for t in tags]

    def transform_commits(self, commits):
        return [{
            "id": c["id"],
            "message": c["message"].strip(),
            "author_name": c["author"].get("displayName") or c["author"].get("name"),
            "author_email": c["author"].get["emailAddress", "Unspecified"],
            "committer_name": c["committer"].get("displayName") or c["committer"].get("name"),
            "committer_email": c["committer"].get["emailAddress", "Unspecified"],
            "parent_ids": [pid["id"] for pid in c["parents"]]
        } for c in commits]
