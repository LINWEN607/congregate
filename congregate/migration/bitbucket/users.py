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
            obj = []
            obj = user.get("links").get("self")
            user["web_url"] = obj[0]["href"]
            del user["links"]
        if isroot:
            users.pop(root_index)
        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(users, f, indent=4)

        if not quiet:
            self.log.info(
                "Retrieved %d users. Check users.json to see all retrieved users" % len(users))

    def generate_user_data(self, user):
        if user.get("id", None) is not None:
            user.pop("id")
        if self.config.group_sso_provider is not None:
            return self.generate_user_group_saml_post_data(user)
        user["username"] = self.create_valid_username(user)
        user["skip_confirmation"] = True
        user["reset_password"] = self.config.reset_password
        # make sure the blocked user cannot do anything
        user["force_random_password"] = "true" if user["state"] == "blocked" else self.config.force_random_password
        if not self.config.reset_password and not self.config.force_random_password:
            # TODO: add config for 'password' field
            self.log.warning(
                "If both 'reset_password' and 'force_random_password' are False, the 'password' field has to be set")
        if self.config.dstn_parent_id is not None:
            user["is_admin"] = False
        return user

    def block_user(self, user_data):
        try:
            response = self.find_user_by_email_comparison_without_id(
                user_data["email"])
            user_creation_data = self.get_user_creation_id_and_email(response)
            if user_creation_data:
                block_response = self.users_api.block_user(
                    self.config.destination_host,
                    self.config.destination_token,
                    user_creation_data["id"])
                self.log.info("Blocking user {0} email {1} (status: {2})"
                              .format(user_data["username"], user_data["email"], block_response))
                return block_response
        except RequestException, e:
            self.log.error(
                "Failed to block user {0}, with error:\n{1}".format(user_data, e))

    def handle_user_creation_status(self, response, user):
        """
        Used to handle the user creation response.
        :param response: The response from the create_user attempt
        :param user: The user entity (from staged_users.json) not the user_data that we generate
        :return: The ID of either the created user or the user found by email
        """
        if response.status_code == 409:
            self.log.info("User {0} already exists".format(user["email"]))
            try:
                # Try to find the user by email. We either just created this, or it already existed
                response = self.find_user_by_email_comparison_without_id(
                    user["email"])
                return self.get_user_creation_id_and_email(response)
            except RequestException, e:
                self.log.error(
                    "Failed to retrieve user {0} status, due to:\n{1}".format(user, e))
        elif response.status_code == 400:
            self.log.error(
                "Unable to create user due to improperly formatted request:\n{}".format(response.text))
            return {
                "email": user["email"],
                "id": None
            }
        else:
            resp = response.json()
            return {
                "email": resp["email"],
                "id": resp["id"]
            }

    def get_user_creation_id_and_email(self, response):
        if response is not None and response:
            if isinstance(response, list):
                return {
                    "email": response[0]["email"],
                    "id": response[0]["id"]
                }
            elif isinstance(response, dict) and response.get("id", None) is not None:
                return {
                    "email": response["email"],
                    "id": response["id"]
                }

    def append_users(self, users):
        with open("%s/data/users.json" % self.app_path, "r") as f:
            user_file = json.load(f)
        staged_users = []
        for user in filter(None, users):
            for u in user_file:
                if user == u["username"]:
                    staged_users.append(u)
                    self.log.info(
                        "Staging user (%s) [%d/%d]" % (u["username"], len(staged_users), len(users)))
        with open("%s/data/staged_users.json" % self.app_path, "w") as f:
            json.dump(remove_dupes(staged_users), f, indent=4)

    def delete_users(self, dry_run=True, hard_delete=False):
        staged_users = self.get_staged_users()
        for su in staged_users:
            email = su["email"]
            self.log.info("{0}Removing user {1}".format(
                get_dry_log(dry_run), email))
            user = self.find_user_by_email_comparison_without_id(email)
            if user is None:
                self.log.info(
                    "User {} does not exist or has already been removed".format(email))
            elif not dry_run:
                try:
                    if get_timedelta(user["created_at"]) < self.config.max_asset_expiration_time:
                        self.users_api.delete_user(
                            self.config.destination_host,
                            self.config.destination_token,
                            user["id"],
                            hard_delete)
                    else:
                        self.log.info("Ignoring {0}. User existed before {1} hours".format(
                            user["email"], self.config.max_asset_expiration_time))
                except RequestException as re:
                    self.log.error(
                        "Failed to remove user\n{0}\nwith error:\n{1}".format(json_pretty(su), re))
