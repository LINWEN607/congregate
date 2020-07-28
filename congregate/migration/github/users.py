import json
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes
from congregate.migration.github.api.users import UsersApi


class UsersClient(BaseClass):
    def __init__(self):
        super(UsersClient, self).__init__()
        self.users_api = UsersApi(self.config.source_host,
                                  self.config.source_token)

    def retrieve_user_info(self):
        users = self.users_api.get_all_users()
        # List and reformat all GitHub user to GitLab metadata
        data = remove_dupes(users)
        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(data, f, indent=4)

        return data
