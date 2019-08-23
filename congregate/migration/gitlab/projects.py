from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from requests.exceptions import RequestException
from congregate.migration.gitlab.api.projects import ProjectsApi
from urllib import quote_plus
from io import BytesIO
from os import walk
import json


class ProjectsClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        super(ProjectsClient, self).__init__()

    @staticmethod
    def get_full_namespace_path(namespace_prefix, namespace, project_name):
        if len(namespace_prefix) > 0:
            return namespace_prefix + "/" + namespace + "/" + project_name
        return namespace + "/" + project_name

    def search_for_project_with_namespace_path(self, host, token, namespace_prefix, namespace, project_name):
        url_encoded_path = quote_plus(self.get_full_namespace_path(namespace_prefix, namespace, project_name))
        resp = api.generate_get_request(host, token, "projects/%s" % url_encoded_path)
        if resp.status_code == 200:
            return resp.json()
        return None

    def add_members(self, members, id):
        """Adds project members."""
        root_user_present = False
        for member in members:
            if member["id"] == self.config.import_user_id:
                root_user_present = True
            new_member = {
                "user_id": member["id"],
                "access_level": member["access_level"]
            }

            try:
                api.generate_post_request(
                    self.config.destination_host, self.config.destination_token, "projects/%d/members" % id,
                    json.dumps(new_member))
            except RequestException, e:
                self.log.error(e)
                self.log.error(
                    "Member might already exist. Attempting to update access level")
                try:
                    api.generate_put_request(self.config.destination_host, self.config.destination_token,
                                             "projects/%d/members/%d?access_level=%d" % (
                                             id, member["id"], member["access_level"]), data=None)
                except RequestException, e:
                    self.log.error(e)
                    self.log.error(
                        "Attempting to update existing member failed")

        if not root_user_present:
            self.log.info("removing root user from project")
            api.generate_delete_request(self.config.destination_host, self.config.destination_token,
                                        "projects/%d/members/%d" % (id, self.config.import_user_id))

    def add_shared_groups(self, old_id, new_id):
        """Adds the list of groups we share the project with."""
        old_project = self.projects_api.get_project(old_id, self.config.source_host, self.config.source_token).json()
        for group in old_project["shared_with_groups"]:
            path = group["group_full_path"]
            new_group_id = self.get_new_group_id(group["group_name"], path)
            if new_group_id is not None:
                data = {
                    "group_access": group["group_access_level"],
                    "group_id": new_group_id,
                    "expires_at": group["expires_at"]
                }
                try:
                    r = self.projects_api.add_shared_group(self.config.destination_host, self.config.destination_token, new_id, data)
                    if r.status_code == 201:
                        self.log.info("Shared project %d with group %s" % (new_id, path))
                    else:
                        self.log.warn("Failed to share project %d with group %s due to:\n%s" % (new_id, path, r.content))
                except RequestException, e:
                    self.log.error("Projects POST request failed with error:\n%s" % e)

    def get_new_group_id(self, name, path):
        """Returns the group's ID on the destination instance."""
        try:
            groups = api.generate_get_request(self.config.destination_host, self.config.destination_token, "groups?search=%s" % name).json()
            if groups:
                for group in groups:
                    if group["full_path"] == path:
                        return group["id"]
            else:
                self.log.warn("Shared group %s does not exist or is not yet imported" % path)
        except RequestException, e:
            self.log.error("Shared groups GET request failed with error:\n%s" % e)

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
