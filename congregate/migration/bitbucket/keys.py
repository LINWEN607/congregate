from gitlab_ps_utils.misc_utils import is_error_message_present
from gitlab_ps_utils.misc_utils import safe_json_response

from requests.exceptions import RequestException

from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket.base import BitBucketServer
from congregate.migration.gitlab.api.users import UsersApi as GLUsersAPI



class KeysClient(BitBucketServer):
    def __init__(self):
        self.users_api = UsersApi()
        self.glusers_api = GLUsersAPI()
        super().__init__()

    def migrate_bb_user_ssh_keys(self, old_user, new_user):
        try:
            resp = self.users_api.get_user_ssh_keys(old_user)
            ssh_keys = iter(dict(safe_json_response(resp)).get("values"))
            self.log.info(f"Migrating user {old_user} SSH keys")
            for k in ssh_keys:
                error, k = is_error_message_present(k)
                if error or not k:
                    self.log.error(
                        f"Failed to fetch user {old_user} SSH key ({k})")
                    return False
                # Sometimes the label value doesn't exist
                try:
                    title_value = k["label"]
                except KeyError:
                    title_value = f"{old_user} migrated key"
                # Extract relevant data
                extracted_data = {"key": k["text"], "title": title_value}

                self.glusers_api.create_user_ssh_key(
                    self.config.destination_host, self.config.destination_token, new_user.get("id", None), extracted_data)
            return True
        except TypeError as te:
            self.log.error(f"User {old_user} SSH keys {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate user {old_user} SSH keys, with error:\n{re}")
            return False