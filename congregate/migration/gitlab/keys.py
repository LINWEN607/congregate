from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present, strip_protocol
from congregate.helpers.dict_utils import pop_multiple_keys
from congregate.helpers.utils import is_dot_com
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.gitlab.users import UsersClient
from congregate.helpers.mdbc import MongoConnector


class KeysClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.users_api = UsersApi()
        self.instance_api = InstanceApi()
        self.users = UsersClient()
        super().__init__()

    def connect_to_mongo(self):
        return MongoConnector()

    def migrate_project_deploy_keys(self, old_id, new_id, name, mongo=None):
        try:
            d_keys = iter(self.projects_api.get_all_project_deploy_keys(
                old_id, self.config.source_host, self.config.source_token))
            if not mongo:
                mongo = self.connect_to_mongo()
            coll = f"keys-{strip_protocol(self.config.source_host)}"
            for key in d_keys:
                # Remove unused key-values before posting key
                key = pop_multiple_keys(key, ["id", "created_at"])
                resp = self.projects_api.create_new_project_deploy_key(
                    new_id, self.config.destination_host, self.config.destination_token, key)
                # When a key being migrated already exists somewhere on the
                # destination instance
                error, resp = is_error_message_present(resp)
                if resp.status_code == 400 and error and isinstance(resp.json().get("message"), dict):
                    if is_dot_com(self.config.destination_host):
                        # Assuming it was created at some point during the migration
                        if last_key := mongo.safe_find_one(coll, query={"key": key["key"]}, sort=[("created_at", mongo.DESCENDING)]):
                            self.projects_api.enable_deploy_key(
                                new_id, last_key["id"], self.config.destination_host, self.config.destination_token)
                        else:
                            self.log.warning(
                                f"Duplicate deploy key {key} for project {name} (ID: {new_id})\n{resp} - {resp.text}")
                    else:
                        for k in self.instance_api.get_all_instance_deploy_keys(
                                self.config.destination_host, self.config.destination_token):
                            if k and key["key"] == k["key"]:
                                self.projects_api.enable_deploy_key(
                                    new_id, k["id"], self.config.destination_host, self.config.destination_token)
                elif resp.status_code != 201:
                    self.log.error(
                        f"Failed to create deploy key {key} for project {name} (ID: {new_id}), with error:\n{resp} - {resp.text}")
                else:
                    mongo.insert_data(coll, resp.json())
            return True
        except TypeError as te:
            self.log.error(
                "Project {0} deploy keys {1} {2}".format(name, resp, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate deploy keys for project {0}, with error:\n{1}".format(name, re))
            return False
        finally:
            mongo.close_connection()

    def migrate_user_ssh_keys(self, old_user, new_user):
        try:
            email = old_user.get("email", None)
            resp = self.users_api.get_all_user_ssh_keys(old_user.get(
                "id", None), self.config.source_host, self.config.source_token)
            ssh_keys = iter(resp.json())
            self.log.info("Migrating user {} SSH keys".format(email))
            for k in ssh_keys:
                error, k = is_error_message_present(k)
                if error or not k:
                    self.log.error(
                        "Failed to fetch SSH keys ({0}) for user {1}".format(k, email))
                    return False
                # Remove unused key-values before posting key
                k = pop_multiple_keys(k, ["id", "created_at"])
                self.users_api.create_user_ssh_key(
                    self.config.destination_host, self.config.destination_token, new_user.get("id", None), k)
            return True
        except TypeError as te:
            self.log.error("User {0} SSH keys {1} {2}".format(email, resp, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate SSH keys for user {0}, with error:\n{1}".format(email, re))
            return False

    def migrate_user_gpg_keys(self, old_user, new_user):
        try:
            email = old_user.get("email", None)
            resp = self.users_api.get_all_user_gpg_keys(old_user.get(
                "id", None), self.config.source_host, self.config.source_token)
            ssh_keys = iter(resp.json())
            self.log.info("Migrating user {} GPG keys".format(email))
            for k in ssh_keys:
                error, k = is_error_message_present(k)
                if error or not k:
                    self.log.error(
                        "Failed to fetch GPG keys ({0}) for user {1}".format(k, email))
                    return False
                # Remove unused key-values before posting key
                k = pop_multiple_keys(k, ["id", "created_at"])
                self.users_api.create_user_gpg_key(
                    self.config.destination_host, self.config.destination_token, new_user.get("id", None), k)
            return True
        except TypeError as te:
            self.log.error("User {0} GPG keys {1} {2}".format(email, resp, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate GPG keys for user {0}, with error:\n{1}".format(email, re))
            return False
