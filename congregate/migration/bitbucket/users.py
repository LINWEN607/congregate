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
        # List and reformat all Bitbucket Server user to GitLab metadata
        users = [u for u in self.users_api.get_all_users(
            self.config.external_source_url, self.config.external_user_token) if u["id"] != 1]
        self.format_users(users)
        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(remove_dupes(users), f, indent=4)
        return remove_dupes(users)

    def format_users(self, users):
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
            # When formatting project and repo users
            if user.get("permission", None):
                user["access_level"] = user.pop("permission")
            for key in keys_to_delete:
                user.pop(key, None)
        return users
