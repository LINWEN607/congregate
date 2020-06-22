import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.api.users import UsersApi


class UsersClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()  # Group API call from bitbucket server
        self.users_api = UsersApi()  # User API call from bitbucket server
        super(UsersClient, self).__init__()

    def retrieve_user_info(self, host, token):
        # Get all the users from users_api
        users = [u for u in self.users_api.get_all_users(
            host, token) if u["id"] != 1]
        keys_to_delete = [
            "active",
            "deletable",
            "directoryName",
            "lastAuthenticationTimestamp",
            "mutableDetails",
            "mutableGroups",
            "slug",
            "type",
            "links"
        ]
        for user in users:
            user["username"] = user.pop("name")
            user["name"] = user.pop("displayName")
            user["email"] = user.pop("emailAddress")
            user["web_url"] = user["links"]["self"][0]["href"]
            user["state"] = "active"
            for key in keys_to_delete:
                user.pop(key, None)
        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(remove_dupes(users), f, indent=4)
        return remove_dupes(users)
