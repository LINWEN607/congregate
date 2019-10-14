import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api

class DeployKeysClient(BaseClass):

    # NOTICE: No import API for global deploy keys (admin level)
    def list_project_deploy_keys(self, id):
        return api.list_all(self.config.source_host, self.config.source_token, "projects/%d/deploy_keys" % id)

    def __create_new_project_deploy_key(self, id, key):
        return api.generate_post_request(self.config.destination_host, self.config.destination_token, "projects/%d/deploy_keys/" % id, key)

    def migrate_deploy_keys(self, old_id, new_id, name):
        try:
            keys = list(self.list_project_deploy_keys(old_id))
            if keys:
                self.log.info("Migrating project {} deploy keys".format(name))
                for key in keys:
                    # Remove unused key-value before posting key
                    key.pop("id", None)
                    key.pop("created_at", None)
                    self.__create_new_project_deploy_key(new_id, json.dumps(key))
                return True
            else:
                self.log.info("Project {} has no deploy keys".format(name))
        except Exception, e:
            self.log.error("Failed to migrate project {0} deploy keys, with error:\n{1}".format(name, e))
            return False
