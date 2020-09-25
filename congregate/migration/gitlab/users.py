import json

from os import path
from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import get_dry_log, json_pretty, get_timedelta, remove_dupes, rewrite_list_into_dict, read_json_file_into_object
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi


class UsersClient(BaseClass):
    BLOCKED = ["blocked", "ldap_blocked", "deactivated"]

    def __init__(self):
        self.groups_api = GroupsApi()
        self.users_api = UsersApi()
        super(UsersClient, self).__init__()
        self.sso_hash_map = self.generate_hash_map()

    def get_staged_users(self):
        return read_json_file_into_object("{}/data/staged_users.json".format(self.app_path))

    def find_user_by_email_comparison_with_id(self, old_user_id):
        self.log.info("Searching for user email by ID {}".format(old_user_id))
        old_user = self.users_api.get_user(
            old_user_id,
            self.config.source_host,
            self.config.source_token).json()
        if old_user is not None and old_user and old_user.get("email", None) is not None:
            self.log.info("Found by old user ID email {0} and user:\n{1}"
                          .format(old_user.get("email", None), json_pretty(old_user)))
            return self.find_user_by_email_comparison_without_id(old_user["email"])
        else:
            self.log.error("Could not by old user ID {0} email of user:\n{1}"
                           .format(old_user_id, json_pretty(old_user)))
        return None

    def find_user_by_email_comparison_without_id(self, email, src=False):
        """
        Find a user by email address in the destination system
        :param email: the email address to check for
        :param src: Is this the source or destination system? True if source else False. Defaults to False.
        :return: The user entity found or None
        """
        self.log.info("Searching for user email {0} in {1} system".format(
            email, "source" if src else "destination"))
        users = self.users_api.search_for_user_by_email(
            self.config.source_host if src else self.config.destination_host,
            self.config.source_token if src else self.config.destination_token,
            email)
        # Will searching for an explicit email actually return more than one? Probably is just an array of 1
        for user in users:
            if user and user.get("email", None) and user["email"].lower() == email.lower():
                self.log.info("Found user by email {}".format(email))
                return user
            else:
                self.log.error(
                    "Could not find user based on email {}".format(email))
        return None

    def username_exists(self, old_user):
        index = 0
        username = old_user["username"]
        is_group = self.is_username_group_name(old_user)
        if is_group is None:
            # None will only come back in error conditions.
            # As such, assume it does exist and try the upstream uniqueness techniques
            return True
        if not is_group:
            # Wasn't found as a group, and wasn't None (error) so check user as actual username
            for user in self.users_api.search_for_user_by_username(
                    self.config.destination_host,
                    self.config.destination_token,
                    username):
                if user["username"].lower() == username.lower():
                    return True
                elif index > 100:
                    # Now that `search_for_user_by_username` uses username= explicitly, is this even necessary?
                    return False
                index += 1
            return False
        else:
            self.log.info(
                "Username {0} for user {1} exists as a group name".format(username, old_user))
            return True

    def is_username_group_name(self, old_user):
        """
        Check if a username exists as a group name
        :param old_user: The source user we are trying to create a new user for
        :return: True if the username from old_user exists as a group name
                None this will signifies "we don't know. do what you will."
                Else False
        """
        try:
            username = str(old_user["username"])
            namespace_check_response = []
            for group in self.groups_api.search_for_group(
                username,
                host=self.config.destination_host,
                token=self.config.destination_token
            ):
                namespace_check_response.append(group)
            if namespace_check_response:
                for z in namespace_check_response:
                    if z.get("path", None) is not None and str(z["path"]).lower() == username.lower():
                        # We found a match, so username is group name. Return True
                        return True
            return False
        except Exception as e:
            self.log.error(
                "Error checking username is not group name for user {0} with error {1}."
                    .format(old_user, e)
            )
            return None

    def user_email_exists(self, old_user):
        index = 0
        if old_user.get("email"):
            email = old_user["email"]
            for user in self.users_api.search_for_user_by_email(self.config.destination_host, self.config.destination_token, email):
                if user.get("email", None) == email:
                    return True
                elif index > 100:
                    return False
                index += 1
        return False

    def find_user_primarily_by_email(self, user):
        new_user = None
        if user:
            if user.get("email", None) is not None:
                new_user = self.find_user_by_email_comparison_without_id(
                    user["email"])
            elif user.get("id", None) is not None:
                new_user = self.find_user_by_email_comparison_with_id(
                    user["id"])
        return new_user

    def find_or_create_impersonation_token(self, user, users_map, expiration_date):
        email = user["email"]
        uid = user["id"]
        if users_map.get(email, None) is None:
            data = {
                "name": "temp_migration_token",
                "expires_at": expiration_date,
                "scopes": [
                    "api"
                ]
            }
            new_impersonation_token = self.users_api.create_user_impersonation_token(
                self.config.destination_host,
                self.config.destination_token,
                uid,
                data).json()
            users_map[email] = new_impersonation_token
            users_map[email]["user_id"] = uid
        return users_map[email]

    def generate_user_group_saml_post_data(self, user):
        identities = user.pop("identities", None)
        extern_uid = self.generate_extern_uid(
            user, identities)
        if extern_uid:
            user["extern_uid"] = extern_uid
            user["group_id_for_saml"] = self.config.dstn_parent_id
            user["provider"] = "group_saml"
            user["reset_password"] = self.config.reset_password
            # make sure the blocked user cannot do anything
            user["force_random_password"] = "true" if user["state"] in self.BLOCKED else self.config.force_random_password
            if not self.config.reset_password and not self.config.force_random_password:
                # TODO: add config for 'password' field
                self.log.warning(
                    "If both 'reset_password' and 'force_random_password' are False, the 'password' field has to be set")
            user["skip_confirmation"] = True
            user["username"] = self.create_valid_username(user)

        return user

    def generate_extern_uid(self, user, identities):
        if self.config.group_sso_provider_pattern == "email":
            return user.get("email", None)
        elif self.config.group_sso_provider_pattern == "hash":
            if email := user.get("email", None):
                if map_user := self.sso_hash_map.get(email, None):
                    return map_user["externalid"]
        else:
            return self.find_extern_uid_by_provider(identities, self.config.group_sso_provider)

    def find_extern_uid_by_provider(self, identities, provider):
        if identities:
            for identity in identities:
                if provider == identity["provider"]:
                    return identity["extern_uid"]
        return None

    def create_valid_username(self, user):
        username = user["username"]
        # If the user email does not exist in the destination system
        if not self.user_email_exists(user):
            # But the username does exist
            if self.username_exists(user):
                # Concat the suffix
                return self.build_suffix_username(username)
        # If you don't find the email, you've attempted to create a suffix-unique username
        # We really should loop over this until we find a non-dupe, but if the company name is used, there really
        # shouldn't be one
        else:
            # We found the email. We should set the username to the email username
            # This means we're going to attempt to create the same user at some point, which is fine
            # However, this also messes up some of our remapping efforts, as those match on source username
            # and not email
            found_by_email_user = self.find_user_by_email_comparison_without_id(
                user["email"])
            if found_by_email_user and found_by_email_user.get("username", None):
                return found_by_email_user["username"]
        return username

    def build_suffix_username(self, username):
        # Concat the suffix
        if self.config.username_suffix is not None:
            return "{0}_{1}".format(username, self.config.username_suffix)
        else:
            self.log.error(
                "Username suffix not set. Defaulting to a single underscore following the username")
            return "{0}_".format(username)

    def add_users_to_parent_group(self, dry_run=True):
        user_results_path = "%s/data/user_migration_results.json" % self.app_path
        if path.exists(user_results_path):
            new_users = read_json_file_into_object(user_results_path)
            for user in new_users:
                if new_users[user].get("id"):
                    data = {
                        "user_id": new_users[user]["id"],
                        "access_level": 10
                    }
                    self.log.info("{0}Adding user {1} to parent group {3} (data: {2}) with guest permissions".format(
                        get_dry_log(dry_run),
                        new_users[user]["email"],
                        data,
                        self.config.dstn_parent_id))

                    if not dry_run:
                        try:
                            self.groups_api.add_member_to_group(
                                self.config.dstn_parent_id, self.config.destination_host, self.config.destination_token, data)
                        except RequestException as e:
                            self.log.error(
                                "Failed to add user {0} to parent group, with error:\n{1}".format(user, e))
        else:
            self.log.error("%s not found" % user_results_path)

    def remove_users_from_parent_group(self, dry_run=True):
        count = 0
        users = self.groups_api.get_all_group_members(
            self.config.dstn_parent_id,
            self.config.destination_host,
            self.config.destination_token)
        for user in users:
            level = user["access_level"]
            if level <= 20:
                count += 1
                self.log.info("{0}Removing user {1} from parent group (access level: {2})".format(
                    get_dry_log(dry_run),
                    user["username"],
                    level))
                if not dry_run:
                    self.groups_api.remove_member(
                        self.config.dstn_parent_id,
                        user["id"],
                        self.config.destination_host,
                        self.config.destination_token)
            else:
                self.log.info("Keeping user {0} in parent group (access level: {1})".format(
                    user["username"],
                    level))
        return count

    def update_user_permissions(self, access_level, dry_run=True):
        PERMISSIONS = {
            "guest": 10,
            "reporter": 20,
            "developer": 30,
            "maintainer": 40,
            "owner": 50}
        level = PERMISSIONS[access_level.lower()]
        try:
            users = list(self.groups_api.get_all_group_members(
                self.config.dstn_parent_id,
                self.config.destination_host,
                self.config.destination_token))
            for user in users:
                self.log.info("{0}Updating {1}'s access level to {2} ({3})".format(
                    get_dry_log(dry_run),
                    user["username"],
                    access_level,
                    level))
                if not dry_run:
                    response = self.groups_api.update_member_access_level(
                        self.config.destination_host,
                        self.config.destination_token,
                        self.config.dstn_parent_id,
                        user["id"],
                        level)
                    if response.status_code != 200:
                        self.log.warning("Failed to update {0}'s parent access level ({1})".format(
                            user["username"],
                            response.content))
                    else:
                        self.log.info("Updated {0}'s parent access level to {1} ({2})".format(
                            user["username"],
                            access_level,
                            level))
        except RequestException as e:
            self.log.error(
                "Failed to update user's parent access level, with error:\n{}".format(e))

    def remove_blocked_users(self, dry_run=True):
        """
            Remove users with state "blocked" from staged users, groups and projects
        """
        self.log.info(
            "{}Removing blocked users from staged users/groups/projects".format(get_dry_log(dry_run)))
        # From staged users
        self.remove("staged_users", dry_run)
        # From staged groups
        self.remove("staged_groups", dry_run)
        # From staged projects
        self.remove("staged_projects", dry_run)

    def remove(self, data, dry_run=True):
        staged = read_json_file_into_object(
            "{0}/data/{1}.json".format(self.app_path, data))

        if data == "staged_users":
            to_pop = []
            for user in staged:
                if user.get("state", None) in self.BLOCKED:
                    to_pop.append(staged.index(user))
                    self.log.info("Removing blocked user {0} from {1}".format(
                        user["username"], data))
            staged = [i for j, i in enumerate(staged) if j not in to_pop]
        else:
            for s in staged:
                to_pop = []
                for member in s["members"]:
                    if member.get("state", None) in self.BLOCKED:
                        to_pop.append(s["members"].index(member))
                        self.log.info("Removing blocked user {0} from {1} ({2})".format(
                            member["username"], data, s["name"]))
                s["members"] = [i for j, i in enumerate(
                    s["members"]) if j not in to_pop]

        if not dry_run:
            with open("{0}/data/{1}.json".format(self.app_path, data), "w") as f:
                f.write(json_pretty(staged))

        return staged

    def search_for_staged_users(self):
        """
        Read the information in staged_users.json and dump to new_users.json and users_not_found.json. Does the
        search based on the email address and *not* username
        :return:
        """
        staged_users = self.get_staged_users()
        new_users = []
        users_not_found = {}
        # Duplicate emails
        duplicate_users = [u for u in staged_users if [s["email"]
                                                       for s in staged_users].count(u["email"]) > 1]
        for user in staged_users:
            email = user.get("email", None)
            state = user.get("state", None)
            new_user = self.find_user_by_email_comparison_without_id(email)
            if new_user:
                new_users.append({
                    "id": new_user.get("id", None),
                    "email": new_user.get("email", None),
                    "state": new_user.get("state", None)
                })
            else:
                self.log.warning(
                    "Could not find user by email {0}. User should have been already migrated".format(email))
                users_not_found[user.get("id", None)] = {
                    "email": email, "state": state}
        self.log.info("Users found ({0}):\n{1}".format(
            len(new_users), "\n".join(json_pretty(u) for u in new_users)))
        self.log.info("Users NOT found ({0}):\n{1}".format(
            len(users_not_found), json_pretty(users_not_found)))
        self.log.info("Duplicate users ({0}):\n{1}".format(
            len(duplicate_users), json_pretty(duplicate_users)))
        return users_not_found, new_users

    def handle_users_not_found(self, data, users, keep=True):
        """
            Remove only FOUND (or NOT FOUND) users from staged users.
            Remove users NOT found from staged users, groups and projects.
            Users NOT found input comes from search_for_staged_users.
            :return: Staged users
        """
        staged = read_json_file_into_object(
            "{0}/data/{1}.json".format(self.app_path, data))

        if data == "staged_users":
            self.log.info("{0} only NOT found users ({1}/{2}) in staged users".format(
                "Keeping" if keep else "Removing", len(users), len(staged)))
            if keep:
                staged = [i for j, i in enumerate(
                    staged) if i["id"] in users.keys()]
            else:
                staged = [i for j, i in enumerate(
                    staged) if i["id"] not in users.keys()]
        else:
            self.log.info("Removing NOT found users ({0}) from staged {1}".format(
                len(users),
                "projects" if data == "staged_projects" else "groups"))
            for s in staged:
                s["members"] = [i for j, i in enumerate(
                    s["members"]) if i["id"] not in users.keys()]
        with open("{0}/data/{1}.json".format(self.app_path, data), "w") as f:
            json.dump(staged, f, indent=4)

        return staged

    def retrieve_user_info(self, host, token):
        if self.config.src_parent_group_path:
            users = []
            for user in self.groups_api.get_all_group_members(self.config.src_parent_id, host, token):
                users.append(self.users_api.get_user(
                    user["id"], host, token).json())
        else:
            users = self.users_api.get_all_users(host, token)

        # Remove root user
        users = [u for u in users if u["id"] != 1]
        keys_to_delete = [
            "web_url",
            "last_sign_in_at",
            "last_activity_at",
            "current_sign_in_at",
            "created_at",
            "confirmed_at",
            "last_activity_on",
            "bio",
            "bio_html",
            # SSO causes issues with the avatar URL due to the authentication
            "avatar_url" if self.config.group_sso_provider else ""
        ]
        for user in users:
            user["email"] = user["email"].lower()
            for key in keys_to_delete:
                user.pop(key, None)

        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(remove_dupes(users), f, indent=4)
        return remove_dupes(users)

    def generate_user_data(self, user):
        if user.get("id", None) is not None:
            user.pop("id")
        if self.config.group_sso_provider is not None:
            return self.generate_user_group_saml_post_data(user)
        user["username"] = self.create_valid_username(user)
        user["skip_confirmation"] = True
        user["reset_password"] = self.config.reset_password
        # make sure the blocked user cannot do anything
        user["force_random_password"] = "true" if user["state"] in self.BLOCKED else self.config.force_random_password
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
        except RequestException as e:
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
            except RequestException as e:
                self.log.error(
                    "Failed to retrieve user {0} status, due to:\n{1}".format(user, e))
        elif response.status_code == 400:
            return self.log_and_return_failed_user_creation(
                "Unable to create user due to improperly formatted request:\n{}".format(response.text), user["email"])
        elif response.status_code == 500:
            return self.log_and_return_failed_user_creation(
                "Unable to create user due to internal server error:\n{}".format(response.text), user["email"])
        else:
            resp = response.json()
            return {
                "email": resp["email"],
                "id": resp["id"]
            }

    def log_and_return_failed_user_creation(self, message, email):
        self.log.error(message)
        return {
            "email": email,
            "id": None
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
        user_file = read_json_file_into_object(
            "%s/data/users.json" % self.app_path)
        staged_users = []
        for user in filter(None, users):
            for u in user_file:
                if user == u["username"]:
                    staged_users.append(u)
                    self.log.info(
                        "Staging user (%s) [%d/%d]" % (u["email"], len(staged_users), len(users)))
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

    def generate_hash_map(self):
        if self.config.group_sso_provider_pattern == "hash":
            if self.config.group_sso_provider_map_file:
                try:
                    hmap = read_json_file_into_object(
                        f"{self.config.group_sso_provider_map_file}")
                    if isinstance(hmap, list):
                        return rewrite_list_into_dict(hmap, "email")
                    return hmap
                except FileNotFoundError:
                    self.log.error(
                        f"{self.config.group_sso_provider_map_file} not found")
                    return None
            self.log.warning(
                "SSO pattern is currently set to hash, but no file is specified in congregate.conf")
        return None
