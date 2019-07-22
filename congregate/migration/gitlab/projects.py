from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from requests.exceptions import RequestException
from urllib import quote_plus
from io import BytesIO
from os import walk
import json


class ProjectsClient(BaseClass):

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

    def search_for_project(self, host, token, name):
        return api.list_all(host, token, "projects?search=%s" % quote_plus(name))

    def get_project(self, id, host, token):
        return api.generate_get_request(host, token, "projects/%d" % id)

    def get_members(self, id, host, token):
        return api.list_all(host, token, "projects/%d/members" % id)

    def add_member_to_group(self, id, host, token, member):
        return api.generate_post_request(host, token, "projects/%d/members" % id, json.dumps(member))

    def archive_project(self, host, token, id):
        return api.generate_post_request(host, token, "projects/%d/archive" % id, {}).json()

    def unarchive_project(self, host, token, id):
        return api.generate_post_request(host, token, "projects/%d/unarchive" % id, {}).json()

    def add_members(self, members, id):
        root_user_present = False
        for member in members:
            if member["id"] == self.config.parent_user_id:
                root_user_present = True
            new_member = {
                "user_id": member["id"],
                "access_level": member["access_level"]
            }

            try:
                api.generate_post_request(
                    self.config.parent_host, self.config.parent_token, "projects/%d/members" % id,
                    json.dumps(new_member))
            except RequestException, e:
                self.log.error(e)
                self.log.error(
                    "Member might already exist. Attempting to update access level")
                try:
                    api.generate_put_request(self.config.parent_host, self.config.parent_token,
                                             "projects/%d/members/%d?access_level=%d" % (
                                             id, member["id"], member["access_level"]), data=None)
                except RequestException, e:
                    self.log.error(e)
                    self.log.error(
                        "Attempting to update existing member failed")

        if not root_user_present:
            self.log.info("removing root user from project")
            api.generate_delete_request(self.config.parent_host, self.config.parent_token,
                                        "projects/%d/members/%d" % (id, self.config.parent_user_id))

    def __old_project_avatar(self, id):
        old_project = self.get_project(
            id, self.config.child_host, self.config.child_token).json()
        return old_project["avatar_url"]

    def migrate_avatar(self, new_id, old_id):
        old_project_avatar = self.__old_project_avatar(old_id)
        if old_project_avatar is not None:
            img = api.generate_get_request(
                self.config.child_host, self.config.child_token, None, url=old_project_avatar)
            filename = old_project_avatar.split("/")[-1]
            headers = {
                'Private-Token': self.config.parent_token
            }
            return api.generate_put_request(self.config.parent_host, self.config.parent_token, "projects/%d" % new_id,
                                            {}, headers=headers, files={
                    'avatar': (filename, BytesIO(img.content))})
        return None

    def migrate_avatar_locally(self, new_id, old_id, file_path):
        old_project_avatar = self.__old_project_avatar(old_id)
        if bool(old_project_avatar):
            for _, _, filename in walk("%s/avatar"):
                avatar = filename[0]
            with open("%s/avatar/%s" % (file_path, avatar), 'rb') as f:
                img = f.read()
            headers = {
                'Private-Token': self.config.parent_token
            }
            return api.generate_put_request(self.config.parent_host, self.config.parent_token, "projects/%d" % new_id,
                                            {}, headers=headers, files={
                    'avatar': (avatar, BytesIO(img))})
        return None

    def find_project_by_path(self, host, token, full_parent_namespace, namespace, name):
        project = self.search_for_project_with_namespace_path(host, token, full_parent_namespace, namespace, name)
        if project is not None:
            if project.get("path_with_namespace", None) is not None:
                if project["path_with_namespace"] == self.get_full_namespace_path(full_parent_namespace, namespace, name):
                    self.log.info("Project already exists. Skipping %s" % name)
                    project_exists = True
                    project_id = project["id"]
                    return project_exists, project_id
        return False, None