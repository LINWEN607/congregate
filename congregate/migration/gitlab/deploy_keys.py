import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.migration.gitlab.projects import ProjectsClient


class DeployKeysClient(BaseClass):
    def __init__(self):
        self.projects = ProjectsClient()
        super(DeployKeysClient, self).__init__()

    # TODO: No import API for global deploy keys (admin level)
    def __list_all_deploy_keys(self, host, token):
        return api.list_all(host, token, "deploy_keys")

    def __list_project_deploy_keys(self, host, token, id):
        return api.list_all(host, token, "projects/%d/deploy_keys" % id)

    def __create_new_project_deploy_key(self, host, token, id, key):
        return api.generate_post_request(host, token, "projects/%d/deploy_keys/" % id, key)

    def migrate_deploy_keys(self, new_id, old_id):
        keys = self.__list_project_deploy_keys(self.config.child_host, self.config.child_token, old_id)
        if keys:
            for key in  keys:
                # Remove unused key-value before posting key
                key.pop("id", None)
                key.pop("created_at", None)
                self.__create_new_project_deploy_key(self.config.parent_host, self.config.parent_token, new_id, json.dumps(key))
