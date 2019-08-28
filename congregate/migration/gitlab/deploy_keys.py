import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api

class DeployKeysClient(BaseClass):

    # NOTICE: No import API for global deploy keys (admin level)
    def list_project_deploy_keys(self, id):
        return api.list_all(self.config.source_host, self.config.source_token, "projects/%d/deploy_keys" % id)

    def __create_new_project_deploy_key(self, id, key):
        return api.generate_post_request(self.config.destination_host, self.config.destination_token, "projects/%d/deploy_keys/" % id, key)

    def migrate_deploy_keys(self, new_id, keys):
        for key in keys:
            # Remove unused key-value before posting key
            key.pop("id", None)
            key.pop("created_at", None)
            self.__create_new_project_deploy_key(new_id, json.dumps(key))
