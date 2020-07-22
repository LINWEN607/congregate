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
        # List and reformat all Bitbucket Server user to GitLab metadata
        users = self.users_api.get_all_users()
        # data = remove_dupes(self.format_users(users))
        data = remove_dupes(users)
        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(data, f, indent=4)
        return data

    def format_users(self, users):
        data = []
        for user in [u for u in users if u["id"] != 1]:
            data.append({
                "id": user["id"],
                "username": user["slug"],
                "name": user["displayName"],
                "email": user["emailAddress"].lower(),
                "web_url": user["links"]["self"][0]["href"],
                "state": "active"
            })
            # When formatting project and repo users
            if user.get("permission", None):
                data[-1]["access_level"] = user["permission"]
        return data
