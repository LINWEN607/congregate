from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import is_error_message_present, strip_netloc
from gitlab_ps_utils.dict_utils import pop_multiple_keys
from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.utils import is_dot_com
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.gitlab.users import UsersClient


class KeysClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.users_api = UsersApi()
        self.instance_api = InstanceApi()
        self.users = UsersClient()
        super().__init__()

    def migrate_project_deploy_keys(self, old_id, new_id, path, mongo=None):
        try:
            src_host = self.config.source_host
            src_keys = iter(self.projects_api.get_all_project_deploy_keys(
                old_id, src_host, self.config.source_token))
            if not mongo:
                mongo = MongoConnector()
            coll = f"keys-{strip_netloc(src_host)}"
            for key in src_keys:
                # Remove unused key-values before posting key
                key = pop_multiple_keys(key, ["id", "created_at"])
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
            self.log.warning(
                f"Duplicate project '{path}' deploy key {key} on destination")
            return False
        for k in self.instance_api.get_all_instance_deploy_keys(host, token):
            if k and key["key"] == k["key"]:
                enable_resp = self.projects_api.enable_deploy_key(
                    new_id, k["id"], host, token)
                return self.handle_deploy_key_enable(enable_resp, path, key)
        self.log.warning(
            f"Project '{path}' deploy key {key} NOT found on destination")
        return False

    def handle_deploy_key_enable(self, resp, path, key):
        if resp.status_code != 201:
            self.log.error(
                f"Failed to enable project '{path}' deploy key {key}, with error:\n{resp} - {resp.text}")
            return False
        return True

    def migrate_user_ssh_keys(self, old_user, new_user):
        try:
            email = old_user.get("email", None)
            resp = self.users_api.get_all_user_ssh_keys(old_user.get(
                "id", None), self.config.source_host, self.config.source_token)
            ssh_keys = iter(resp.json())
            self.log.info(f"Migrating user {email} SSH keys")
            for k in ssh_keys:
                error, k = is_error_message_present(k)
                if error or not k:
                    self.log.error(
                        f"Failed to fetch user {email} SSH key ({k})")
                    return False
                # Remove unused key-values before posting key
                k = pop_multiple_keys(k, ["id", "created_at"])
                self.users_api.create_user_ssh_key(
                    self.config.destination_host, self.config.destination_token, new_user.get("id", None), k)
            return True
        except TypeError as te:
            self.log.error(f"User {email} SSH keys {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate user {email} SSH keys, with error:\n{re}")
            return False

    def migrate_user_gpg_keys(self, old_user, new_user):
        try:
            email = old_user.get("email", None)
            resp = self.users_api.get_all_user_gpg_keys(old_user.get(
                "id", None), self.config.source_host, self.config.source_token)
            ssh_keys = iter(resp.json())
            self.log.info(f"Migrating user {email} GPG keys")
            for k in ssh_keys:
                error, k = is_error_message_present(k)
                if error or not k:
                    self.log.error(
                        f"Failed to fetch user {email} GPG key ({k})")
                    return False
                # Remove unused key-values before posting key
                k = pop_multiple_keys(k, ["id", "created_at"])
                self.users_api.create_user_gpg_key(
                    self.config.destination_host, self.config.destination_token, new_user.get("id", None), k)
            return True
        except TypeError as te:
            self.log.error(f"User {email} GPG keys {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate user {email} GPG keys, with error:\n{re}")
            return False
