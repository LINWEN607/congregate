from gitlab_ps_utils.misc_utils import strip_netloc, is_error_message_present

from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket.base import BitBucketServer
from congregate.helpers.mdbc import MongoConnector


class Client(BitBucketServer):
    def __init__(self):
        self.users_api = UsersApi()
        super().__init__()

    def migrate_bb_user_ssh_keys(self, old_user, new_user):
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