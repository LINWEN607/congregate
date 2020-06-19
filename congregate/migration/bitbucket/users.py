import json

from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.helpers.misc_utils import get_dry_log, json_pretty, get_timedelta
from congregate.helpers.misc_utils import remove_dupes
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.api.users import UsersApi


class UsersClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi() # Group API call from bitbucket server
        self.users_api = UsersApi() # User API call from bitbucket server
        super(UsersClient, self).__init__()

    def get_staged_users(self):
        with open("{}/data/staged_users.json".format(self.app_path), "r") as f:
            return json.load(f)

    def retrieve_user_info(self, host, token):
        # Get all the users from users_api
        users = list(self.users_api.get_all_users(host, token))
        root_index = None
        isroot = False
        for user in users:
            # Removing root user
            if user["id"] == 1:
                isroot = True
                root_index = users.index(user)
            else:
                keys_to_delete = [
                    "active",
                    "deletable",
                    "directoryName",
                    "lastAuthenticationTimestamp",
                    "mutableDetails",
                    "mutableGroups",
                    "slug",
                    "type"
                ]
                for key in keys_to_delete:
                    if key in user:
                        user.pop(key)            
            user["username"] = user.pop("name")
            user["name"] = user.pop("displayName")
            user["email"] = user.pop("emailAddress")
            user["web_url"] = user["links"]["self"][0]["href"]
            user.pop("links")
        if isroot:
            users.pop(root_index)
        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(users, f, indent=4)

        self.log.info(
            "Retrieved %d users. Check users.json to see all retrieved users" % len(users))


