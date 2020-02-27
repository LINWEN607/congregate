import json
from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.helpers.misc_utils import get_dry_log


class BranchesClient(BaseClass):
    def __init__(self):
        self.users = UsersApi()
        self.groups = GroupsApi()
        self.projects = ProjectsApi()
        super(BranchesClient, self).__init__()

    def get_branches(self, pid, host, token):
        return api.list_all(host, token, "projects/%d/repository/branches" % pid)

    def get_protected_branches(self, pid, host, token):
        return api.list_all(host, token, "projects/%d/protected_branches" % pid)

    def set_default_branch(self, pid, host, token, branch):
        return api.generate_put_request(host, token, "projects/%d?default_branch=%s" % (pid, branch), data=None)

    def update_default_branch(self, old_id, new_id, old_project=None):
        try:
            if not old_project:
                old_project = self.projects.get_project(
                    old_id, self.config.source_host, self.config.source_token).json()
            if old_project.get("default_branch", None) is not None:
                default_branch = old_project["default_branch"]
                name = old_project["name"]
                self.log.info(
                    "Setting default branch to {0} for project {1}".format(default_branch, name))
                self.set_default_branch(
                    new_id,
                    self.config.destination_host,
                    self.config.destination_token,
                    default_branch)
            return True
        except RequestException as re:
            self.log.error(
                "Failed to migrate project {0} default branch, with error:\n{1}".format(name, re))
            return False

    def protect_branch(self, id, host, token, branch_name, push_access_level=None, merge_access_level=None, allowed_to_push=None, allowed_to_merge=None, allowed_to_unprotect=None):
        data = {
            "name": branch_name
        }
        if push_access_level is not None:
            data["push_access_level"] = push_access_level
        if merge_access_level is not None:
            data["merge_access_level"] = merge_access_level
        if allowed_to_push is not None:
            data["allowed_to_push"] = allowed_to_push
        if allowed_to_merge is not None:
            data["allowed_to_merge"] = allowed_to_merge
        if allowed_to_unprotect is not None:
            data["allowed_to_unprotect"] = allowed_to_unprotect
        return api.generate_post_request(host, token, "projects/%d/protected_branches" % id, json.dumps(data))

    def update_access_levels(self, access_level):
        for a in access_level:
            if a.get("user_id", None) is not None:
                user = self.users.get_user(
                    a["user_id"], self.config.source_host, self.config.source_token).json()
                new_user = api.search(
                    self.config.destination_host, self.config.destination_token, 'users', user['email'])
                new_user_id = new_user[0]["id"]
                a["user_id"] = new_user_id
            if a.get("group_id", None) is not None:
                group = self.groups.get_group(
                    a["group_id"], self.config.source_host, self.config.source_token).json()
                if self.config.parent_id is not None:
                    parent_group = self.groups.get_group(
                        self.config.parent_id, self.config.destination_host, self.config.destination_token).json()
                    group["full_path"] = "%s/%s" % (
                        parent_group["full_path"], group["full_path"])
                for new_group in self.groups.search_for_group(group["name"], self.config.destination_host, self.config.destination_token):
                    if new_group["full_path"].lower() == group["full_path"].lower():
                        a["group_id"] = new_group["id"]
                        break

        return access_level

    def migrate_protected_branches(self, old_id, new_id, name):
        try:
            response = iter(self.get_protected_branches(
                old_id,
                self.config.source_host,
                self.config.source_token))
            p_branches = iter(response)
            for branch in p_branches:
                allowed_to_push = self.update_access_levels(
                    branch["push_access_levels"])
                allowed_to_merge = self.update_access_levels(
                    branch["merge_access_levels"])
                allowed_to_unprotect = self.update_access_levels(
                    branch["unprotect_access_levels"])
                self.log.info("Migrating project {0} (ID: {1}) protected branche {2}".format(
                    name, old_id, branch["name"]))
                self.protect_branch(
                    new_id,
                    self.config.destination_host,
                    self.config.destination_token,
                    branch["name"],
                    allowed_to_push=allowed_to_push,
                    allowed_to_merge=allowed_to_merge,
                    allowed_to_unprotect=allowed_to_unprotect)
        except TypeError as te:
            self.log.error(
                "Project {0} protected branches {1} {2}".format(name, response, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate protected branches for {0}, with error:\n{1}".format(name, re))
            return False
        else:
            return True

    def set_default_branches_to_master(self, dry_run=True):
        for project in self.projects.get_all_projects(self.config.destination_host, self.config.destination_token):
            if project.get("default_branch", None) == "master":
                path = project["path_with_namespace"]
                self.log.info("{0}Setting project {1} default branch to master".format(
                    get_dry_log(dry_run), path))
                if not dry_run:
                    try:
                        resp = self.set_default_branch(
                            project["id"],
                            self.config.destination_host,
                            self.config.destination_token,
                            "master")
                        self.log.info(
                            "Project {0} default branch set to master ({1})".format(path, resp))
                    except RequestException, e:
                        self.log.error(
                            "Failed to set project {0} default branch to master, with error:\n{1}".format(path, e))
