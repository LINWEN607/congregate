from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import is_error_message_present, strip_netloc
from gitlab_ps_utils.dict_utils import pop_multiple_keys
from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.utils import is_dot_com
from congregate.migration.github.api.repos import ReposApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.instance import InstanceApi


class KeysClient(BaseClass):
    def __init__(self):
        super().__init__()
        self.repos_api = ReposApi(self.config.source_host, self.config.source_token)
        self.projects_api = ProjectsApi()
        self.instance_api = InstanceApi()

    def migrate_project_deploy_keys(self, new_id, repo, mongo=None):
        try:
            owner = repo["namespace"]
            path = repo["path"]
            src_host = self.config.source_host
            src_keys = iter(self.repos_api.get_all_repo_deploy_keys(
                owner, path))
            if not mongo:
                mongo = MongoConnector()
            coll = f"keys-{strip_netloc(src_host)}"
            for key in src_keys:
                # Remove unused key-values before posting key
                key = pop_multiple_keys(key, ["id", "verified", "created_at", "read_only", "added_by", "last_used"])
                resp = self.projects_api.create_new_project_deploy_key(
                    new_id, self.config.destination_host, self.config.destination_token, key)
                if resp.status_code == 201:
                    mongo.insert_data(coll, resp.json())
                    continue
                # When a key being migrated already exists somewhere on the
                # destination instance
                if resp.status_code == 400 and is_error_message_present(
                        resp)[0] and isinstance(resp.json().get("message"), dict):
                    return self.handle_failed_deploy_key_create(mongo, coll, key, new_id, path)
                self.log.error(
                    f"Failed to create project '{path}' deploy key {key}, with error:\n{resp} - {resp.text}")
                return False
            return True
        except TypeError as te:
            self.log.error(f"Project '{path}' deploy keys {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate project '{path}' deploy keys, with error:\n{re}")
            return False
        finally:
            mongo.close_connection()

    def handle_failed_deploy_key_create(self, mongo, coll, key, new_id, path):
        host = self.config.destination_host
        token = self.config.destination_token
        if is_dot_com(host):
            # Assuming it was created at some point during the migration
            if last_key := mongo.safe_find_one(coll, query={"key": key["key"]}, sort=[
                    ("created_at", mongo.DESCENDING)]):
                enable_resp = self.projects_api.enable_deploy_key(
                    new_id, last_key["id"], host, token)
                return self.handle_deploy_key_enable(enable_resp, path, key)
        for k in self.instance_api.get_all_instance_deploy_keys(host, token):
            if k and key["key"] == k["key"]:
                enable_resp = self.projects_api.enable_deploy_key(
                    new_id, k["id"], host, token)
                return self.handle_deploy_key_enable(enable_resp, path, key)
            self.log.warning(
                f"Duplicate project '{path}' deploy key {key} on destination")
            return False
        self.log.warning(
            f"Project '{path}' deploy key {key} NOT found on destination")
        return False

    def handle_deploy_key_enable(self, resp, path, key):
        if resp.status_code != 201:
            self.log.error(
                f"Failed to enable project '{path}' deploy key {key}, with error:\n{resp} - {resp.text}")
            return False
        return True
