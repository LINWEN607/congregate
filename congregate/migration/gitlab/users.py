from os import path
import copy
import json
from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.helpers.misc_utils import get_dry_log, json_pretty
from congregate.helpers.threads import handle_multi_thread
from congregate.helpers.misc_utils import remove_dupes, migration_dry_run
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi


class UsersClient(BaseClass):
    def __init__(self):
        self.groups_api = GroupsApi()
        self.users_api = UsersApi()
        super(UsersClient, self).__init__()

    def get_staged_users(self):
        with open("{}/data/staged_users.json".format(self.app_path), "r") as f:
            return json.load(f)

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
            if user is not None and \
                    user and \
                    user.get("email", None) is not None and \
                    user["email"].lower() == email.lower():
                self.log.info("Found by email {0} user:\n{1}".format(
                    email, json_pretty(user)))
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
                    if z.get("name", None) is not None and str(z["name"]).lower() == username.lower():
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
            for user in self.users_api.search_for_user_by_email(self.config.destination_host, self.config.destination_token,
                                                                email):
                if user["email"] == email:
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

    def find_or_create_impersonation_token(self, host, token, user, users_map, expiration_date):
        email = user["email"]
        id = user["id"]
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
                id,
                data).json()
            users_map[email] = new_impersonation_token
            users_map[email]["user_id"] = id
        return users_map[email]

    def generate_user_group_saml_post_data(self, user):
        identities = user.pop("identities")
        user["external"] = True
        user["group_id_for_saml"] = self.config.parent_id
        user["extern_uid"] = self.find_extern_uid_by_provider(
            identities, self.config.group_sso_provider)
        user["provider"] = "group_saml"
        user["reset_password"] = self.config.reset_password
        # make sure the blocked user cannot do anything
        user["force_random_password"] = "true" if user["state"] == "blocked" else self.config.force_random_password
        if not self.config.reset_password and not self.config.force_random_password:
            # TODO: add config for 'password' field
            self.log.warning(
                "If both 'reset_password' and 'force_random_password' are False, the 'password' field has to be set")
        user["skip_confirmation"] = True
        user["username"] = self.create_valid_username(user)

        return user

    def find_extern_uid_by_provider(self, identities, provider):
        for identity in identities:
            if provider == identity["provider"]:
                return identity["extern_uid"]

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

    def update_users(self, obj, new_users, obj_type):
        """
        Scan the obj JSON (usually staged projects or staged groups) and replace old user ids
        with the info from new_users. Calls to the source system to match those IDs based on email
        :param obj: Usually the data from stage.json (projects) or staged_groups.json
        :param new_users: The content of new_users.json (or similar) that will be used to find the destination ID
        :return:
        """

        not_found_all = []
        not_found_members = []
        # An email-index dictionary of the new user objects
        rewritten_users = {}
        for i in range(len(new_users)):
            new_obj = new_users[i]
            user_email = str(new_users[i]["email"]).lower()

            # Create a username based dictionary of the new_users.json objects
            rewritten_users[user_email] = new_obj

        for i in range(len(obj)):
            self.log.info("Rewriting users for {0} {1}".format(
                obj_type, obj[i]["name"]))
            members = obj[i]["members"]
            if isinstance(members, list):
                for member in members:
                    # Get the old user from the source system by ID
                    self.log.info(
                        "Searching on source for user ID {0}".format(member["id"]))
                    old_user = self.users_api.get_user(
                        member["id"], self.config.source_host, self.config.source_token)
                    old_user = old_user.json()

                    if old_user.get("email"):
                        old_user_email = str(old_user.get("email")).lower()

                        if rewritten_users.get(old_user_email, None) is not None:
                            rewritten_user = rewritten_users[old_user_email]
                            self.log.info("Searching on destination by ID {0} for user email {1}".format(
                                rewritten_user["id"],
                                old_user_email))
                            new_user = self.users_api.get_user(
                                rewritten_user["id"],
                                self.config.destination_host,
                                self.config.destination_token).json()
                            if new_user.get("message", None) is None and \
                                    new_user.get("email", None) is not None and \
                                    str(new_user["email"]).lower() == old_user_email:
                                # If we find the user by new ID, and the emails match (as they should by this point
                                # as these users are either newly created or found by email, earlier)
                                # reassign the user ids in the object (staged project or staged group)
                                # Assign the member id to the *new* member id. We've checked this
                                # many times by this point, so some of the searches may be redundant, but sane
                                member["id"] = rewritten_user["id"]
                                continue

                    # In all other cases, default the action to the import_user_id
                    not_found_members.append(copy.deepcopy(member))
                    member["id"] = self.config.import_user_id

            not_found_all.append({obj[i]["name"]: not_found_members})
            not_found_members = []

        self.log.warning("Members NOT found in {0}s: {1}"
                         .format(obj_type, json_pretty(not_found_all)))
        return obj

    def map_new_users_to_groups_and_projects(self, dry_run=True):
        """
        Kind of a dupe of update_new_users. Has the benefit of the dry_run flag
        :param dry_run: If true, don't actually write the updates to stage or staged_groups
        :return: Nothing
        """
        with open("%s/data/stage.json" % self.app_path, "r") as f:
            staged_projects = json.load(f)

        with open("%s/data/staged_groups.json" % self.app_path, "r") as f:
            staged_groups = json.load(f)

        new_users_dir = "{}/data/new_users.json".format(self.app_path)
        if path.exists(new_users_dir):
            with open(new_users_dir, "r") as f:
                new_users = json.load(f)
        else:
            self.log.info("All users have already been migrated.")
            return

        staged_projects = self.update_users(
            staged_projects, new_users, "project")
        staged_groups = self.update_users(staged_groups, new_users, "group")

        self.log.info("{}Mapping missing (destination) users to staged projects and groups"
                      .format(get_dry_log(dry_run)))
        if not dry_run:
            with open("%s/data/stage.json" % self.app_path, "wb") as f:
                json.dump(staged_projects, f, indent=4)
            with open("%s/data/staged_groups.json" % self.app_path, "wb") as f:
                json.dump(staged_groups, f, indent=4)

    def add_users_to_parent_group(self, dry_run=True):
        with open("%s/data/newer_users.json" % self.app_path, "r") as f:
            new_users = json.load(f)

        for user in new_users:
            data = {
                "user_id": user["id"],
                "access_level": 10
            }
            self.log.info("{0}Adding user {1} to parent group (data: {2})".format(
                get_dry_log(dry_run),
                user["email"],
                data))
            if not dry_run:
                try:
                    self.groups_api.add_member_to_group(
                        self.config.parent_id, self.config.destination_host, self.config.destination_token, data)
                except RequestException, e:
                    self.log.error(
                        "Failed to add user {0} to parent group, with error:\n{1}".format(user, e))

    def remove_users_from_parent_group(self, dry_run=True):
        count = 0
        users = self.groups_api.get_all_group_members(
            self.config.parent_id,
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
                        self.config.parent_id,
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
                self.config.parent_id,
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
                        self.config.parent_id,
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
        except RequestException, e:
            self.log.error(
                "Failed to update user's parent access level, with error:\n{}".format(e))

    def remove_blocked_users(self, dry_run=True):
        """
            Remove users with state "blocked" from staged users, groups and projects
        """
        self.log.info(
            "{}Removing blocked users form staged users/groups/projects".format(get_dry_log(dry_run)))
        # From staged users
        self.remove("staged_users", dry_run)
        # From staged groups
        self.remove("staged_groups", dry_run)
        # From staged projects
        self.remove("stage", dry_run)

    def remove(self, data, dry_run=True):
        with open("{0}/data/{1}.json".format(self.app_path, data), "r") as f:
            staged = json.load(f)

        if data == "staged_users":
            to_pop = []
            for user in staged:
                if user.get("state", None) == "blocked":
                    to_pop.append(staged.index(user))
                    self.log.info("Removing blocked user {0} from {1}".format(
                        user["username"], data))
            staged = [i for j, i in enumerate(staged) if j not in to_pop]
        else:
            for s in staged:
                to_pop = []
                for member in s["members"]:
                    if member.get("state", None) == "blocked":
                        to_pop.append(s["members"].index(member))
                        self.log.info("Removing blocked user {0} from {1} ({2})".format(
                            member["username"], data, s["name"]))
                s["members"] = [i for j, i in enumerate(
                    s["members"]) if j not in to_pop]

        if not dry_run:
            with open("{0}/data/{1}.json".format(self.app_path, data), "w") as f:
                f.write(json_pretty(staged))

        return staged

    # TODO: Re-use or remove (does not show users to be removed)
    def remove_blocked_users_dry_run(self):
        # create a 'newer_users.json' file with only non-blocked users
        count = 0
        with open("%s/data/new_users.json" % self.app_path, "r") as f:
            new_users = json.load(f)
        with open("%s/data/users.json" % self.app_path, "r") as f:
            users = json.load(f)

        newer_users = []

        rewritten_users = {}
        for i in range(len(users)):
            new_obj = users[i]
            id_num = users[i]["username"]
            rewritten_users[id_num] = new_obj

        rewritten_users_by_name = {}
        for i in range(len(users)):
            new_obj = users[i]
            id_num = users[i]["name"]
            rewritten_users_by_name[id_num] = new_obj

        for new_user in new_users:
            key = new_user["username"]
            if rewritten_users.get(key, None) is not None:
                if rewritten_users[key]["state"] == "blocked":
                    count += 1
                else:
                    newer_users.append(new_user)
            else:
                key = new_user["name"]
                if rewritten_users_by_name.get(key, None) is not None:
                    if rewritten_users_by_name[key]["state"] == "blocked":
                        count += 1
                    else:
                        newer_users.append(new_user)
        self.log.info("Newer user count after blocking ({0}). {1} to remove".format(
            len(newer_users), count))

        with open("%s/data/newer_users.json" % self.app_path, "wb") as f:
            json.dump(newer_users, f, indent=4)

    def update_user_info(self, new_ids, overwrite=True):
        """
        Update the user ids in stage.json (projects) and staged_groups.json with the proper user ids via a call
        to update_users as pulled from new_users.json.
        By default, rewrite (overwrite) the new_users.json file before doing this with freshly found info based on the
        ids
        :param new_ids: The list of user ids from found (email) or created users
        :param overwrite: Rewrite the new_users.json file with the user information returned from a find on
                            new_ids. Default as True.
        :return: No return
        """

        if overwrite:
            with open("%s/data/new_users.json" % self.app_path, "w") as f:
                new_users = []
                for new_id in new_ids:
                    new_user = self.users_api.get_user(
                        new_id["id"], self.config.destination_host, self.config.destination_token).json()
                    if isinstance(new_user, list):
                        new_users.append(new_user[0])
                    elif isinstance(new_user, dict):
                        new_users.append(new_user)

                root_index = None
                for user in new_users:
                    if user["id"] == 1:
                        root_index = new_users.index(user)
                        break
                if root_index:
                    new_users.pop(root_index)

                json.dump(new_users, f, indent=4)

        with open("%s/data/stage.json" % self.app_path, "r") as f:
            staged_projects = json.load(f)

        with open("%s/data/staged_groups.json" % self.app_path, "r") as f:
            staged_groups = json.load(f)

        with open("%s/data/new_users.json" % self.app_path, "r") as f:
            new_users = json.load(f)

        staged_projects = self.update_users(
            staged_projects, new_users, "project")
        staged_groups = self.update_users(staged_groups, new_users, "group")

        with open("%s/data/stage.json" % self.app_path, "wb") as f:
            json.dump(staged_projects, f, indent=4)

        with open("%s/data/staged_groups.json" % self.app_path, "wb") as f:
            json.dump(staged_groups, f, indent=4)

    def update_staged_user_info(self, dry_run=True):
        """
        Read the information in staged_users.json and dump to new_users.json and users_not_found.json. Does the
        search based on the email address and *not* username
        :return:
        """
        staged_users = self.get_staged_users()
        new_users = []
        users_not_found = {}
        for user in staged_users:
            self.log.info("Searching for user email {}".format(user["email"]))
            # Try to find a user in the destination system by email
            new_user = api.search(
                self.config.destination_host,
                self.config.destination_token,
                'users',
                user['email']
            )

            # If we find the user by email, but didn't get the email field back (will happen if you are not using
            # an admin token for search) set the email field
            if len(new_user) > 1:
                self.log.error(
                    "Too many users found for email search using email {0}".format(user["email"]))
                users_not_found[user["id"]] = user["email"]
            elif len(new_user) > 0:
                if new_user[0].get("email", None) is None:
                    new_user[0]["email"] = user["email"]
                # Add to new_users
                new_users.append(new_user[0])
            else:
                self.log.warning(
                    "Could not find user by email {0}. User should have been already migrated"
                    .format(user["email"])
                )
                users_not_found[user["id"]] = user["email"]

        # Add extra IDs based on manually created file data/ids.txt
        other_ids = []
        if path.isfile("%s/data/ids.txt" % self.app_path):
            with open("%s/data/ids.txt" % self.app_path, "r") as f:
                for line in f.readlines():
                    other_ids.append(int(line))

        # Search for users by ID. If you find those, also add them to new_users
        for other_id in other_ids:
            self.log.info("Searching for user {} (ID)".format(other_id))
            new_user = self.users_api.get_user(
                other_id, self.config.destination_host, self.config.destination_token).json()
            new_users.append(new_user)

        if not dry_run:
            # Dump everything found in new_users (email from staged or ids.txt)
            with open("%s/data/new_users.json" % self.app_path, "w") as f:
                json.dump(new_users, f, indent=4)
            # Users not found will only include those not found by the email search
            with open("%s/data/users_not_found.json" % self.app_path, "w") as f:
                json.dump(users_not_found, f, indent=4)

        self.log.info("{0}Users found ({1}):\n{2}".format(
            get_dry_log(dry_run),
            len(new_users),
            "\n".join(u["email"] for u in new_users)))
        self.log.info("{0}Users NOT found ({1}):\n{2}".format(
            get_dry_log(dry_run),
            len(users_not_found),
            json_pretty(users_not_found)))

        return users_not_found

    def handle_users_not_found(self, data, users, keep=True):
        """
            Remove FOUND users from staged users.
            Remove users NOT found from staged users, groups and projects.
            Users NOT found input comes from update_staged_user_info.
            :return: Staged users
        """
        with open("{0}/data/{1}.json".format(self.app_path, data), "r") as f:
            staged = json.load(f)

        if data == "staged_users":
            self.log.info("{0} all but the NOT found users ({1}) from staged users".format(
                "Removing" if keep else "Keeping",
                len(users)))
            if keep:
                staged = [i for j, i in enumerate(
                    staged) if i["id"] in users.keys()]
            else:
                staged = [i for j, i in enumerate(
                    staged) if i["id"] not in users.keys()]
        else:
            self.log.info("Removing the NOT found users ({0}) from staged {1}".format(
                len(users),
                "projects" if data == "stage" else "groups"))
            for s in staged:
                s["members"] = [i for j, i in enumerate(
                    s["members"]) if i["id"] not in users.keys()]

        with open("{0}/data/{1}.json".format(self.app_path, data), "w") as f:
            f.write(json_pretty(staged))

        return staged

    def retrieve_user_info(self, host, token, quiet=False):
        users = list(api.list_all(host,
                                  token, "users"))
        root_index = None
        for user in users:
            # Removing root user
            if user["id"] == 1:
                root_index = users.index(user)
            else:
                keys_to_delete = [
                    "avatar_url",
                    "web_url",
                    "bio",
                    "location",
                    "skype",
                    "linkedin",
                    "twitter",
                    "last_sign_in_at",
                    "last_activity_at",
                    "current_sign_in_at",
                    "can_create_project",
                    "created_at",
                    "confirmed_at",
                    "last_activity_on",
                    "theme_id",
                    "color_scheme_id"
                ]
                for key in keys_to_delete:
                    if key in user:
                        user.pop(key)

        if root_index:
            users.pop(root_index)

        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(users, f, indent=4)

        if not quiet:
            self.log.info(
                "Retrieved %d users. Check users.json to see all retrieved users" % len(users))

    def migrate_user_info(self, dry_run=True):
        staged_users = self.get_staged_users()

        if not dry_run:
            new_ids = []
            new_ids = handle_multi_thread(
                self.handle_user_creation, staged_users)
            return list(filter(None, new_ids))
        else:
            self.log.info(
                "DRY-RUN: Outputing various USER migration data to dry_run_user_migration.json")
            migration_dry_run("user", handle_multi_thread(
                self.generate_user_data, staged_users))

    def generate_user_data(self, user):
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
        if self.config.parent_id is not None:
            user["is_admin"] = False
        return user

    def handle_user_creation(self, user):
        """
        This is called when importing staged_users.json.
        Blocked users will be skipped if we do NOT 'keep_blocked_users'.
        :param user: Each iterable called is a user from the staged_users.json file
        :return:
        """
        try:
            if user.get("state", None) \
                    and (str(user["state"]).lower() == "active"
                         or (str(user["state"]).lower() == "blocked"
                             and self.config.keep_blocked_users)):
                user_data = self.generate_user_data(user)
                self.log.info(
                    "Attempting to create user:\n{}".format(json_pretty(user)))
                response = self.users_api.create_user(
                    self.config.destination_host,
                    self.config.destination_token,
                    user_data)
            else:
                response = None
        except RequestException, e:
            self.log.error(
                "Failed to create user {0}, with error:\n{1}".format(user_data, e))
            response = None

        if response is not None:
            try:
                self.log.info(
                    "User creation response text was {}".format(response.text))
            except Exception as e:
                self.log.error(
                    "Could not get response text. Error was {0}".format(e))
            try:
                self.log.info("User creation response JSON was:\n{}".format(
                    json_pretty(response.json())))
            except Exception as e:
                self.log.error(
                    "Could not get response JSON. Error was {0}".format(e))

            # NOTE: Persist 'blocked' user state regardless of domain and creation status.
            if user_data.get("state", None) and str(user_data["state"]).lower() == "blocked":
                self.block_user(user_data)
            return self.handle_user_creation_status(response, user_data)
        return None

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
        else:
            resp = response.json()
            return {
                "id": resp["id"],
                "email": resp["email"]
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
        for user in users:
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
            self.log.info("Removing user {}".format(su["email"]))
            user = self.find_user_by_email_comparison_without_id(su["email"])
            if user is None:
                self.log.info(
                    "User {} does not exist or has already been removed".format(su["email"]))
            elif not dry_run:
                try:
                    self.users_api.delete_user(
                        self.config.destination_host,
                        self.config.destination_token,
                        user["id"],
                        hard_delete)
                except RequestException, e:
                    self.log.error(
                        "Failed to remove user {0}\nwith error: {1}".format(su, e))
