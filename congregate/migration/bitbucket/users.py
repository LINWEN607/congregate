import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.api.users import UsersApi


class UsersClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.users_api = UsersApi()
        super(UsersClient, self).__init__()

    def retrieve_user_info(self):
        """
        List and transform all Bitbucket Server user to GitLab user metadata
        """
        users = self.users_api.get_all_users(
            self.config.source_host)
        data = remove_dupes(self.format_users(users))
        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(data, f, indent=4)
        return data

    def format_users(self, users):
        data = []
        for user in [u for u in users if u["id"] != 1]:
            if user.get("emailAddress", None):
                data.append({
                    "id": user["id"],
                    "username": user["slug"],
                    "name": user["displayName"],
                    "email": user["emailAddress"].lower(),
                    "state": "active"
                })
                # When formatting project and repo users
                if user.get("permission", None):
                    data[-1]["access_level"] = user["permission"]
        return data
