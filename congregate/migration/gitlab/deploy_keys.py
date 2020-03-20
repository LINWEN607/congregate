from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present
from congregate.migration.gitlab.api.projects import ProjectsApi


class DeployKeysClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        super(DeployKeysClient, self).__init__()

    def migrate_deploy_keys(self, old_id, new_id, name):
        try:
            resp = self.projects_api.get_all_project_deploy_keys(
                old_id, self.config.source_host, self.config.source_token)
            d_keys = iter(resp)
            self.log.info("Migrating project {} deploy keys".format(name))
            for key in d_keys:
                if is_error_message_present(key):
                    self.log.error(
                        "Failed to fetch deploy keys ({0}) for project {1}".format(key, name))
                    return False
                # Remove unused key-value before posting key
                key.pop("id", None)
                key.pop("created_at", None)
                self.projects_api.create_new_project_deploy_key(
                    new_id, self.config.destination_host, self.config.destination_token, key)
            return True
        except TypeError as te:
            self.log.error(
                "Project {0} deploy keys {1} {2}".format(name, resp, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate deploy keys for project {0}, with error:\n{1}".format(name, re))
            return False
