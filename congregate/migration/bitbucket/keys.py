from gitlab_ps_utils.misc_utils import strip_netloc, is_error_message_present
from gitlab_ps_utils.dict_utils import pop_multiple_keys

from requests.exceptions import RequestException
import json

from congregate.migration.bitbucket.api.users import UsersApi
from congregate.migration.bitbucket.base import BitBucketServer
from congregate.helpers.mdbc import MongoConnector
from congregate.migration.gitlab.api.users import UsersApi as GLUsersAPI


class KeysClient(BitBucketServer):
    def __init__(self):
        self.users_api = UsersApi()
        self.glusers_api = GLUsersAPI()
        super().__init__()

    def migrate_bb_user_ssh_keys(self, old_user, new_user):
        try:
            email = old_user.get("email", None)
            resp = self.users_api.get_user_ssh_keys(old_user.get("id"))
            ssh_keys = iter(resp.json())
            self.log.info(f"Migrating user {email} SSH keys")
            for k in ssh_keys:
                error, k = is_error_message_present(k)
                if error or not k:
                    self.log.error(
                        f"Failed to fetch user {email} SSH key ({k})")
                    return False
                # Extract relevant data
                data = json.loads(k)
                values_list = data["values"]
                extracted_data = {"text": values_list[0]["text"], "label": values_list[0]["label"]}

                self.glusers_api.create_user_ssh_key(
                    self.config.destination_host, self.config.destination_token, new_user.get("id", None), extracted_data)
            return True
        except TypeError as te:
            self.log.error(f"User {email} SSH keys {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate user {email} SSH keys, with error:\n{re}")
            return False