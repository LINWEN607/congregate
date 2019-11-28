import json
from urllib import quote_plus
from io import BytesIO
from os import walk
from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.migration.gitlab.api.projects import ProjectsApi


class ProjectsClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        super(ProjectsClient, self).__init__()

    @staticmethod
    def get_full_namespace_path(namespace_prefix, namespace, project_name):
        if len(namespace_prefix) > 0:
            return namespace_prefix + "/" + namespace + "/" + project_name
        return namespace + "/" + project_name

    def get_staged_projects(self):
        with open("{}/data/stage.json".format(self.app_path), "r") as f:
            return json.load(f)

    def search_for_project_with_namespace_path(self, host, token, namespace_prefix, namespace, project_name):
        url_encoded_path = quote_plus(self.get_full_namespace_path(namespace_prefix, namespace, project_name))
        resp = api.generate_get_request(host, token, "projects/%s" % url_encoded_path)
        if resp.status_code == 200:
            return resp.json()
        return None

    def add_members(self, members, id):
        """Adds project members."""
        for member in members:
            # If we do not keep_blocked_users skip adding
            if member.get("state", None) is not None \
                    and str(member["state"]).lower() == "blocked" \
                    and not self.config.keep_blocked_users:
                continue
            new_member = {
                "user_id": member["id"],
                "access_level": member["access_level"]
            }
            try:
                self.projects_api.add_member(
                    id,
                    self.config.destination_host,
                    self.config.destination_token,
                    new_member)
            except RequestException, e:
                self.log.error("Member might already exist. Attempting to update access level despite error:\n{}".format(e))
                try:
                    api.generate_put_request(
                        self.config.destination_host,
                        self.config.destination_token,
                        "projects/{0}/members/{1}?access_level={2}".format(
                            id,
                            member["id"],
                            member["access_level"]),
                            data=None)
                except RequestException, e:
                    self.log.error("Attempting to update existing member failed, with error:\n{}".format(e))

        self.remove_import_user_from_project(id)

    def root_user_present(self, members):
        for member in members:
            if member["id"] == self.config.import_user_id:
                return True
        return False
            
    def remove_import_user_from_project(self, id):
        try:
            self.log.info("Removing import (root) user from project")
            self.projects_api.remove_member(
                id,
                self.config.import_user_id,
                self.config.destination_host,
                self.config.destination_token)
        except RequestException, e:
            self.log.error("Failed to remove import (root) user from project, with error:\n{}".format(e))

    def add_shared_groups(self, old_id, new_id):
        """Adds the list of groups we share the project with."""
        old_project = self.projects_api.get_project(old_id, self.config.source_host, self.config.source_token).json()
        project_name = old_project["name"]
        for group in old_project["shared_with_groups"]:
            path = group["group_full_path"]
            name = group["group_name"]
            new_group_id = self.get_new_group_id(name, path)
            if new_group_id is not None:
                data = {
                    "group_access": group["group_access_level"],
                    "group_id": new_group_id,
                    "expires_at": group["expires_at"]
                }
                try:
                    r = self.projects_api.add_shared_group(self.config.destination_host, self.config.destination_token, new_id, data)
                    if r.status_code == 201:
                        self.log.info("Shared project {0} with group {1}".format(project_name, name))
                    else:
                        self.log.warn("Failed to share project {0} with group {1} due to:\n{2}".format(project_name, name, r.content))
                except RequestException, e:
                    self.log.error("Failed to POST shared group {0} to project {1}, with error:\n{2}".format(name, project_name, e))

    def get_new_group_id(self, name, path):
        """Returns the group's ID on the destination instance."""
        try:
            groups = api.generate_get_request(self.config.destination_host, self.config.destination_token, "groups?search=%s" % name).json()
            if groups:
                for group in groups:
                    if group["full_path"] == path:
                        return group["id"]
            else:
                self.log.warn("Shared group {} does not exist or is not yet imported".format(path))
        except RequestException, e:
            self.log.error("Failed to GET group {0} ID, with error:\n{1}".format(name, e))

    def __old_project_avatar(self, id):
        """Returns the source project avatar."""
        old_project = self.projects_api.get_project(
            id, self.config.source_host, self.config.source_token).json()
        return old_project["avatar_url"]

    def migrate_avatar(self, new_id, old_id):
        """Assigns the project avatar from memory."""
        old_project_avatar = self.__old_project_avatar(old_id)
        if old_project_avatar is not None:
            img = api.generate_get_request(
                self.config.source_host, self.config.source_token, None, url=old_project_avatar)
            filename = old_project_avatar.split("/")[-1]
            headers = {
                'Private-Token': self.config.destination_token
            }
            return api.generate_put_request(self.config.destination_host, self.config.destination_token, "projects/%d" % new_id,
                                            {}, headers=headers, files={
                    'avatar': (filename, BytesIO(img.content))})
        return None

    def migrate_avatar_locally(self, new_id, old_id, file_path):
        """Assigns the project avatar from a locally stored image."""
        old_project_avatar = self.__old_project_avatar(old_id)
        if bool(old_project_avatar):
            for _, _, filename in walk("%s/avatar"):
                avatar = filename[0]
            with open("%s/avatar/%s" % (file_path, avatar), 'rb') as f:
                img = f.read()
            headers = {
                'Private-Token': self.config.destination_token
            }
            return api.generate_put_request(self.config.destination_host, self.config.destination_token, "projects/%d" % new_id,
                                            {}, headers=headers, files={
                    'avatar': (avatar, BytesIO(img))})
        return None

    def find_project_by_path(self, host, token, full_parent_namespace, namespace, name):
        """Returns a tuple (project_exists, ID) based on path."""
        project = self.search_for_project_with_namespace_path(host, token, full_parent_namespace, namespace, name)
        if project is not None:
            if project.get("path_with_namespace", None) is not None:
                if project["path_with_namespace"] == self.get_full_namespace_path(full_parent_namespace, namespace, name):
                    self.log.info("Project already exists. Skipping %s" % name)
                    return True, project["id"]
        return False, None

    def get_path_with_namespace(self, project):
        return "{0}{1}/{2}".format(
            self.config.parent_group_path + "/" if self.config.parent_group_path else "",
            project["namespace"],
            project["name"])

    def delete_projects(self, dry_run=True):
        staged_projects = self.get_staged_projects()
        for sp in staged_projects:
            # SaaS destination instances have a parent group
            path_with_namespace = self.get_path_with_namespace(sp)
            self.log.info("Removing project {}".format(path_with_namespace))
            resp = self.projects_api.get_project_by_path_with_namespace(
                path_with_namespace,
                self.config.destination_host,
                self.config.destination_token)
            if resp is not None:
                if resp.status_code != 200:
                    self.log.info("Project {0} does not exist (status: {1})".format(path_with_namespace, resp.status_code))
                elif not dry_run:
                    try:
                        self.projects_api.delete_project(
                            self.config.destination_host,
                            self.config.destination_token,
                            resp.json()["id"])
                    except RequestException, e:
                        self.log.error("Failed to remove project {0}\nwith error: {1}".format(sp, e))
            else:
                self.log.error("Failed to GET project {} by path_with_namespace".format(path_with_namespace))

    def update_project_badges(self, new_id, name, full_parent_namespace):
        badges = self.projects_api.get_all_project_badges(
            self.config.destination_host,
            self.config.destination_token,
            new_id)
        if badges:
            badges = list(badges)
            if badges:
                self.log.info("Updating project {0} badges".format(name))
                self.update_badges(new_id, full_parent_namespace, badges)
                return True
            else:
                self.log.info("Project {} has no badges".format(name))
        else:
            self.log.warning("Failed to retrieve badges for {0}, with response:\n{1}".format(name, badges))
            return False

    def update_badges(self, new_id, namespace, badges):
        try:
            for badge in badges:
                # split after hostname and retrieve only remaining path
                link_url_suffix = badge["link_url"].split("/", 3)[3]
                image_url_suffix = badge["image_url"].split("/", 3)[3]
                data = {
                    "link_url": "{0}/{1}/{2}".format(self.config.destination_host, namespace, link_url_suffix),
                    "image_url": "{0}/{1}/{2}".format(self.config.destination_host, namespace, image_url_suffix)
                }
                self.projects_api.edit_project_badge(self.config.destination_host,
                    self.config.destination_token,
                    new_id,
                    badge["id"],
                    data=data)
                self.log.info("Updated project {0} (ID) badge {1}".format(new_id, data))
        except RequestException, e:
            self.log.error("Failed to update project {0} (ID) badge {1}, with error:\n{2}".format(new_id, badge, e))
            return False

    def count_unarchived_projects(self):
        unarchived_projects = []
        for project in self.projects_api.get_all_projects(self.config.source_host, self.config.source_token):
            if project.get("archived", None) is not None:
                if not project["archived"]:
                    unarchived_projects.append(project["name_with_namespace"])
        self.log.info("Unarchived projects ({0}):\n{1}".format(unarchived_projects, len(unarchived_projects)))

    def archive_staged_projects(self, dry_run=True):
        staged_projects = self.get_staged_projects()
        self.log.info("Project count is: {}".format(len(staged_projects)))
        try:
            for project in staged_projects:
                pid = project["id"]
                self.log.info("Archiving project {0} (ID: {1})".format(
                    self.get_path_with_namespace(project),
                    pid))
                if not dry_run:
                    self.projects_api.archive_project(
                        self.config.source_host,
                        self.config.source_token,
                        pid)
        except RequestException, e:
            self.log.error("Failed to archive staged projects, with error:\n{}".format(e))

    def unarchive_staged_projects(self, dry_run=True):
        staged_projects = self.get_staged_projects()
        self.log.info("Project count is: {}".format(len(staged_projects)))
        try:
            for project in staged_projects:
                pid = project["id"]
                self.log.info("Unarchiving project {0} (ID: {1})".format(
                    self.get_path_with_namespace,
                    pid))
                if not dry_run:
                    self.projects_api.unarchive_project(
                        self.config.source_host,
                        self.config.source_token,
                        pid)
        except RequestException, e:
            self.log.error("Failed to unarchive staged projects, with error:\n{}".format(e))

    def validate_staged_projects_schema(self):
        with open("%s/data/staged_groups.json" % self.app_path, "r") as f:
            staged_groups = json.load(f)
        for g in staged_groups:
            self.log.info(g)
            if g.get("name", None) is None:
                self.log.warn("name is missing")
            if g.get("namespace", None) is None:
                self.log.warn("namespace is missing")
            if g.get("project_type", None) is None:
                self.log.warn("project_type is missing")
            if g.get("default_branch", None) is None:
                self.log.warn("default_branch is missing")
            if g.get("visibility", None) is None:
                self.log.warn("visibility is missing")
            if g.get("http_url_to_repo", None) is None:
                self.log.warn("http_url_to_repo is missing")
            if g.get("shared_runners_enabled", None) is None:
                self.log.warn("shared_runners_enabled is missing")
            if g.get("members", None) is None:
                self.log.warn("members is missing")
            if g.get("id", None) is None:
                self.log.warn("id is missing")
            if g.get("description", None) is None:
                self.log.warn("description is missing")
