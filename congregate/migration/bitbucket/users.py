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

    def retrieve_user_info(self, host, token, quiet=False):
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
            user["state"] = user.pop("active")            
            user["username"] = user.pop("name")
            user["name"] = user.pop("displayName")
            user["email"] = user.pop("emailAddress")
            obj = []
            obj = user.get("links").get("self")
            user["web_url"] = obj[0]["href"]
            user.pop("links")
        if isroot:
            users.pop(root_index)
        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(users, f, indent=4)

        if not quiet:
            self.log.info(
                "Retrieved %d users. Check users.json to see all retrieved users" % len(users))

    # def generate_user_data(self, user):
    #     if user.get("id", None) is not None:
    #         user.pop("id")
    #     if self.config.group_sso_provider is not None:
    #         return self.generate_user_group_saml_post_data(user)
    #     user["username"] = self.create_valid_username(user)
    #     user["skip_confirmation"] = True
    #     user["reset_password"] = self.config.reset_password
    #     # make sure the blocked user cannot do anything
    #     user["force_random_password"] = "true" if user["state"] == "blocked" else self.config.force_random_password
    #     if not self.config.reset_password and not self.config.force_random_password:
    #         # TODO: add config for 'password' field
    #         self.log.warning(
    #             "If both 'reset_password' and 'force_random_password' are False, the 'password' field has to be set")
    #     if self.config.dstn_parent_id is not None:
    #         user["is_admin"] = False
    #     return user

