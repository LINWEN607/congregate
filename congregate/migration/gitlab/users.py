import os
import sys
from requests import Response
from requests.exceptions import RequestException
from pandas import DataFrame, Series, set_option

from gitlab_ps_utils.misc_utils import get_dry_log, get_timedelta, is_error_message_present, \
    safe_json_response, strip_netloc
from gitlab_ps_utils.json_utils import json_pretty, read_json_file_into_object, write_json_to_file, read_json_file_into_object
from gitlab_ps_utils.dict_utils import rewrite_list_into_dict, rewrite_json_list_into_dict
from gitlab_ps_utils.list_utils import remove_dupes

from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.migrate_utils import get_staged_users, find_user_by_email_comparison_without_id, is_gl_version_older_than
from congregate.helpers.utils import is_dot_com
from congregate.migration.gitlab import constants
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.users import UsersApi


class UsersClient(BaseClass):
    def __init__(self):
        self.groups_api = GroupsApi()
        self.users_api = UsersApi()
        self.projects_api = ProjectsApi()
        super().__init__()
        self.sso_hash_map = self.generate_hash_map()

    def find_user_by_email_comparison_with_id(self, old_user_id):
        self.log.info(f"Searching for user email by ID {old_user_id}")
        old_user = safe_json_response(self.users_api.get_user(
            old_user_id, self.config.source_host, self.config.source_token))
        if old_user and old_user.get("email") is not None:
            self.log.info(
                f"Found by OLD user ID email {old_user.get('email')} and user:\n{json_pretty(old_user)}")
            return find_user_by_email_comparison_without_id(old_user["email"])
        self.log.error(
            f"Could NOT find by OLD user ID {old_user_id} email of user:\n{json_pretty(old_user)}")
        return None

    def username_exists(self, old_user):
        index = 0
        username = old_user["username"]
        is_group = self.is_username_group_name(old_user)
        if is_group is None:
            # None will only come back in error conditions.
            # As such, assume it does exist and try the upstream uniqueness
            # techniques
            return True
        if not is_group:
            # Wasn't found as a group, and wasn't None (error) so check user as
            # actual username
            for user in self.users_api.search_for_user_by_username(
                    self.config.destination_host,
                    self.config.destination_token,
                    username):
                if user["username"].lower() == username.lower():
                    return True
                if index > 100:
                    # Now that `search_for_user_by_username` uses username=
                    # explicitly, is this even necessary?
                    return False
                index += 1
            return False
        self.log.warning(
            f"Username {username} for user {old_user} exists as a group name")
        return True

    def is_username_group_name(self, old_user):
        """
        Check if a username exists as a group namespace
        :param old_user: The source user we are trying to create a new user for
        :return: True if the username from old_user exists as a group namespace
                None signifies "we don't know. do what you will."
                else False
        """
        try:
            username = str(old_user["username"])
            for g in self.groups_api.search_for_group(
                    username, host=self.config.destination_host, token=self.config.destination_token):
                is_error, resp = is_error_message_present(g)
                if is_error:
                    self.log.warning(
                        f"Is '{username}' a group namespace lookup failed for group:\n{resp}")
                elif resp.get("path") and str(resp["path"]).lower() == username.lower():
                    # We found a match, so user=group namespace
                    return True
            return False
        except RequestException as re:
            self.log.error(
                f"Error checking `{username}` is not group namespace for user {old_user} with error:\n{re}")
            return None

    def user_email_exists(self, old_user):
        if old_user.get("email"):
            email = old_user["email"]
            for user in self.users_api.search_for_user_by_email(
                    self.config.destination_host, self.config.destination_token, email):
                if user.get("email") == email:
                    return True
        return False

    def find_user_primarily_by_email(self, user):
        new_user = None
        if user:
            if user.get("email") is not None:
                new_user = find_user_by_email_comparison_without_id(
                    user["email"])
            elif user.get("id") is not None:
                new_user = self.find_user_by_email_comparison_with_id(
                    user["id"])
        return new_user

    def find_or_create_impersonation_token(
            self, user, users_map, expiration_date):
        email = user["email"]
        uid = user["id"]
        if users_map.get(email) is None:
            data = {
                "name": "temp_migration_token",
                "expires_at": expiration_date,
                "scopes": [
                    "api"
                ]
            }
            new_impersonation_token = safe_json_response(self.users_api.create_user_impersonation_token(
                self.config.destination_host,
                self.config.destination_token,
                uid,
                data))
            users_map[email] = new_impersonation_token
            users_map[email]["user_id"] = uid
        return users_map[email]

    def generate_user_group_saml_post_data(self, user):
        if identities := user.pop("identities", None):
            extern_uid = self.generate_extern_uid(
                user, identities)
            if extern_uid:
                user["extern_uid"] = extern_uid
                if self.config.group_sso_provider:
                    provider = str(self.config.group_sso_provider).lower()
                    user["provider"] = provider
                    if provider == "group_saml":
                        user["group_id_for_saml"] = self.config.dstn_parent_id
        user["reset_password"] = self.config.reset_password
        # make sure the inactive user cannot do anything
        user["force_random_password"] = "true" if user["state"] in self.INACTIVE else self.config.force_random_password
        if not self.config.reset_password and not self.config.force_random_password:
            # TODO: add config for 'password' field
            self.log.warning(
                "If both 'reset_password' and 'force_random_password' are False, the 'password' field has to be set")
        user["skip_confirmation"] = True
        user["username"] = self.create_valid_username(user)

        return user

    def generate_extern_uid(self, user, identities):
        if self.config.group_sso_provider_pattern == "email":
            return user.get("email")
        if self.config.group_sso_provider_pattern == "hash":
            email = user.get("email")
            map_user = self.sso_hash_map.get(email)
            if email and map_user:
                return map_user["externalid"]
        else:
            return self.find_extern_uid_by_provider(
                identities, self.config.group_sso_provider)

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
            found_by_email_user = find_user_by_email_comparison_without_id(
                user["email"])
            if found_by_email_user and found_by_email_user.get("username"):
                return found_by_email_user["username"]
        return username

    def build_suffix_username(self, username):
        # Concat the suffix
        suffix = str(self.config.username_suffix).strip("_")
        new_username = f"{username}_{suffix}"
        self.log.warning(
            f"Adding {'(default) ' if suffix == 'migrated' else ''}suffix to username to avoid duplication: '{username}' -> '{new_username}'")
        return new_username

    def update_parent_group_members(self, access_level, add_members=False, dry_run=True):
        target_level = constants.MEMBER_ROLES.get(access_level.lower())
        if target_level is None:
            self.log.error(
                f"Invalid access level entry '{access_level}'"
                f"\nValid entries: {[k for k in constants.MEMBER_ROLES.keys()]})")
            sys.exit(os.EX_DATAERR)
        parent_id = self.config.dstn_parent_id
        if not parent_id:
            self.log.error(
                f"Invalid parent group ID configured ('{parent_id}')")
            sys.exit(os.EX_CONFIG)
        try:
            self.__handle_parent_group_members(
                dry_run, add_members, access_level, target_level)
        except RequestException as re:
            self.log.error(
                f"Failed to {'add or ' if add_members else ''}update parent group {parent_id} members, with error:\n{re}")

    def __handle_parent_group_members(self, dry_run, add_members, access_level, target_level):
        host = self.config.destination_host
        token = self.config.destination_token
        parent_id = self.config.dstn_parent_id
        dry_log = get_dry_log(dry_run=dry_run)
        members = {}

        # List and extract parent member IDs
        for m in self.groups_api.get_all_group_members(parent_id, host, token):
            members[m.get("id")] = m.get("access_level")
        mids = [k for k, _ in members.items()]
        for su in get_staged_users():
            user = find_user_by_email_comparison_without_id(
                su.get("email"))
            if not user:
                continue
            uid = user.get("id")
            username = user.get("username")
            # Invite member with required access level
            if uid not in mids and add_members:
                self.log.info(
                    f"{dry_log}Add user {username} (ID: {uid}) as {access_level}")
                if not dry_run:
                    self.groups_api.add_member_to_group(
                        parent_id, host, token, {"user_id": uid, "access_level": target_level})
                continue
            # Retrieve member parent access level and update
            level = members.get(uid)
            if uid in mids and level != target_level:
                self.log.info(
                    f"{dry_log}Update member {user.get('username')} (ID: {uid}) access level {level} -> {target_level} ({access_level})")
                if not dry_run:
                    self.groups_api.update_member_access_level(
                        host, token, parent_id, uid, target_level)
                continue
            if uid not in mids:
                self.log.warning(
                    f"SKIP: Member {username} (ID: {uid}) not found. Missing '--add-members'?")

    def update_members_access_level(self, current_level, target_level, skip_groups=False, skip_projects=False, dry_run=True):
        current_role = constants.MEMBER_ROLES.get(current_level.lower())
        target_role = constants.MEMBER_ROLES.get(target_level.lower())
        if current_role is None or target_role is None:
            self.log.error(
                f"Invalid access level entry for current '{current_level}' and/or target '{target_level}' access level"
                f"\nValid entries: {[k for k in constants.MEMBER_ROLES.keys()]})")
            sys.exit(os.EX_DATAERR)
        try:
            if not skip_groups:
                self.log.info(f"Updating group member roles '{current_level}' -> '{target_level}'")
                self.__update_members_access_level("group", current_role, target_role, dry_run=dry_run)
            if not skip_projects:
                self.log.info(f"Updating project member roles '{current_level}' -> '{target_level}'")
                self.__update_members_access_level("project", current_role, target_role, dry_run=dry_run)
        except RequestException as re:
            self.log.error(f"Failed to update group/project members access levels:\n{re}")
        except Exception as e:
            self.log.error(f"Failure in update group/project members access levels:\n{e}")

    def __update_members_access_level(self, object_type, current_role, target_role, dry_run=True):
        migration_results = rewrite_json_list_into_dict(
            read_json_file_into_object(
                f"{self.app_path}/data/results/{object_type}_migration_results.json"))

        for k, v in migration_results.items():
            # Otherwise it's the Total/Successful count
            if isinstance(v, dict):
                if oid := v.get("id"):
                    if object_type == "group":
                        self.__update_group_members_access_level(k, oid, current_role, target_role, dry_run=dry_run)
                    else:
                        self.__update_project_members_access_level(k, oid, current_role, target_role, dry_run=dry_run)
                else:
                    self.log.warning(f"Skipping failed {object_type} '{k}' migration:\n{json_pretty(v)}")

    def __update_group_members_access_level(self, g, gid, current_role, target_role, dry_run=True):
        host = self.config.destination_host
        token = self.config.destination_token
        for m in self.groups_api.get_all_group_members(gid, host, token):
            mid = m.get("id")
            username = m.get("username")
            if mid and m.get("access_level") == current_role:
                self.log.info(f"{get_dry_log(dry_run=dry_run)}Updating group '{g}' member '{username}' access level: {current_role} -> {target_role}")
                if not dry_run:
                    self.groups_api.update_member_access_level(host, token, gid, mid, target_role)

    def __update_project_members_access_level(self, p, pid, current_role, target_role, dry_run=True):
        host = self.config.destination_host
        token = self.config.destination_token
        # Including inherited to have the correct access level range
        for m in self.projects_api.get_members_incl_inherited(pid, host, token):
            mid = m.get("id")
            username = m.get("username")
            if mid and m.get("access_level") == current_role:
                self.log.info(f"{get_dry_log(dry_run=dry_run)}Updating project '{p}' member '{username}' access level: {current_role} -> {target_role}")
                if not dry_run:
                    self.projects_api.edit_member(host, token, pid, mid, target_role)

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

    def remove_inactive_users(self, membership=False, dry_run=True):
        """
            Remove inactive users from staged users, groups and projects
        """
        # From staged users
        self.remove("staged_users", dry_run=dry_run)
        # From staged groups
        self.remove("staged_groups", membership, dry_run)
        # From staged projects
        self.remove("staged_projects", membership, dry_run)

    def remove(self, data, membership=False, dry_run=True):
        staged = read_json_file_into_object(
            f"{self.app_path}/data/{data}.json")
        self.log.info(
            f"{get_dry_log(dry_run)}Removing inactive users from {data}")
        if data == "staged_users":
            staged = [u for u in staged if u.get("state") not in self.INACTIVE]
        else:
            is_group = data == "staged_groups"
            for s in staged:
                spath = s.get("full_path") if is_group else s.get(
                    "path_with_namespace")
                self.log.info(
                    f"{get_dry_log(dry_run)}Removing inactive users from {spath} members")
                if (not dry_run) and membership:
                    self.remove_members(s, is_group, spath)
                s["members"] = [m for m in s.get("members", []) if m.get(
                    "state") not in self.INACTIVE]
        if not dry_run:
            write_json_to_file(
                f"{self.app_path}/data/{data}.json", staged, log=self.log)
        return staged

    def remove_members(self, staged, is_group, staged_path):
        try:
            host = self.config.source_host
            token = self.config.source_token
            sid = staged.get("id")
            for m in staged.get("members", []):
                if m.get("state") in self.INACTIVE:
                    if is_group:
                        self.groups_api.remove_member(
                            sid, m.get("id"), host, token)
                    else:
                        self.projects_api.remove_member(
                            sid, m.get("id"), host, token)
        except RequestException as re:
            self.log.error(
                f"Failed to remove {m.get('name')} from {staged_path}, with error:\n{re}")

    def search_for_staged_users(self, table=False):
        """
        Read the information in staged_users.json and output users that are:
            - FOUND on destination
                - State mismatch (e.g. 'active' -> 'blocked')
                - NOT logged in
                - W/O identities
                - Inactive (any non-active state)
            - NOT found on destination
            - Source 'public_email' NOT set or NOT matching primary
            - Duplicate (emails)
        Does the search based on the configured user_mapping_field
        :return:
        """
        staged_users = get_staged_users()
        users_found = []
        users_not_found = {}
        field = self.config.user_mapping_field
        user_mapping = {}

        self.lookup_staged_users(staged_users, users_found, users_not_found, field, user_mapping)

        inactive = [f"{u.get(field)} - {u.get('dest_state')}"
            for u in users_found if u.get("dest_state") in self.INACTIVE]
        state_mismatch = [f"{u.get(field)}: {u.get('src_state')} -> {u.get('dest_state')}"
            for u in users_found if u.get("src_state") != u.get("dest_state")]
        no_login = [f"{u.get(field)} - {u.get('dest_state')}"
            for u in users_found if not u.get("last_sign_in_at")]
        no_identities = [f"{u.get(field)} - {u.get('dest_state')}"
            for u in users_found if not u.get("identities")]
        no_public_email = [f"{u.get(field)}: {u.get('email')} -> {u.get('public_email')}"
            for u in staged_users if u.get("email") != u.get("public_email")]

        duplicate_users = [u for u in staged_users if [s[field] for s in staged_users].count(u[field]) > 1]

        found = f"Found ({len(users_found)})"
        inact = f"Inactive ({len(inactive)})"
        mismatch = f"State mismatch ({len(state_mismatch)})"
        no_log = f"NOT logged in ({len(no_login)})"
        wo_ids = f"W/O identities ({len(no_identities)})"
        not_found = f"NOT found ({len(users_not_found)})"
        pub_email = f"Source 'public_email' NOT set or NOT matching primary ({len(no_public_email)})"
        dupe = f"Duplicate ({len(duplicate_users)})"
        self.log.info(f"""Destination users status:
            {found}:\n{json_pretty(users_found)}
            {inact}:\n{json_pretty(inactive)}
            {mismatch}:\n{json_pretty(state_mismatch)}
            {no_log}:\n{json_pretty(no_login)}
            {wo_ids}:\n{json_pretty(no_identities)}
            {not_found}:\n{json_pretty(users_not_found)}
            {pub_email}:\n{json_pretty(no_public_email)}
            {dupe}:\n{json_pretty(duplicate_users)}
        """)
        if table:
            d = {
                found: Series([f"{u.get(field)} - {u.get('dest_state')}" for u in users_found], dtype=str),
                inact: Series(inactive, dtype=str),
                mismatch: Series(state_mismatch, dtype=str),
                no_log: Series(no_login, dtype=str),
                wo_ids: Series(no_identities, dtype=str),
                not_found: Series([f"{u.get(field)} - {u.get('src_state')}" for u in users_not_found.values()], dtype=str),
                pub_email: Series(no_public_email, dtype=str),
                dupe: Series(
                    [f"{u.get(field)} - {u.get('state')}" for u in duplicate_users], dtype=str)
            }
            set_option('display.max_rows', None)
            set_option('display.max_columns', None)
            set_option('display.width', None)
            set_option('display.max_colwidth', None)
            csv = f"{self.app_path}/data/user_stats.csv"
            self.log.info(
                f"Writing {self.config.destination_host} user stats to {csv}:\n{DataFrame(d)}")
            DataFrame(d).to_csv(csv, sep="\t")

        user_mapping_file = f"{self.app_path}/data/user_mapping_by_{field}.json"
        self.log.info(f"Writing FOUND users by '{field}' src:dest primary email mapping to {user_mapping_file}")
        write_json_to_file(user_mapping_file, user_mapping)
        return users_not_found, users_found

    def lookup_staged_users(self, staged_users, users_found, users_not_found, field, user_mapping):
        for user in staged_users:
            key = user.get(field)
            state = user.get("state")
            dest_user = None
            if field == "email":
                dest_user = find_user_by_email_comparison_without_id(key)
            elif field == "username":
                for u in self.users_api.search_for_user_by_username(
                    self.config.destination_host,
                    self.config.destination_token,
                    key):
                    if u.get(field, "").lower() == user.get(field, "").lower():
                        dest_user = u
                        break
            else:
                self.log.error(f"Invalid user mapping field configured: '{field}'")
                sys.exit(os.EX_CONFIG)
            if dest_user:
                users_found.append({
                    "id": dest_user.get("id"),
                    "email": dest_user.get("email"),
                    "username": dest_user.get("username"),
                    "src_state": state,
                    "dest_state": dest_user.get("state"),
                    "last_sign_in_at": dest_user.get("last_sign_in_at"),
                    "identities": dest_user.get("identities")
                })
                user_mapping[key] = {
                    "src": {
                        "id": user.get("id"),
                        "primary": user.get("email"),
                        "public": user.get("public_email")
                    },
                    "dest": {
                        "id": dest_user.get("id"),
                        "primary": dest_user.get("email"),
                        "public": dest_user.get("public_email")
                    }
                }
            else:
                users_not_found[user.get("id")] = {
                    field: key, "src_state": state}

    def handle_users_not_found(self, data, users, keep=True):
        """
            Remove only FOUND (or NOT FOUND) users from staged users.
            Remove users NOT found from staged users, groups and projects.
            Users NOT found input comes from search_for_staged_users.
            :return: Staged users
        """
        staged = read_json_file_into_object(f"{self.app_path}/data/{data}.json")

        if data == "staged_users":
            self.log.info(f"{'Keeping' if keep else 'Removing'} only NOT found users ({len(users)}/{len(staged)}) in staged users")
            if keep:
                staged = [i for j, i in enumerate(
                    staged) if i["id"] in users.keys()]
            else:
                staged = [i for j, i in enumerate(
                    staged) if i["id"] not in users.keys()]
        else:
            self.log.info(f"Removing NOT found users ({len(users)}) from staged {'projects' if data == 'staged_projects' else 'groups'}")
            for s in staged:
                s["members"] = [i for j, i in enumerate(
                    s["members"]) if i["id"] not in users.keys()]
        write_json_to_file(
            f"{self.app_path}/data/{data}.json", staged, log=self.log)

        return staged

    def retrieve_user_info(self, host, token, processes=None):
        if self.config.src_parent_group_path:
            users = []
            for user in self.groups_api.get_all_group_members(
                    self.config.src_parent_id, host, token):
                users.append(safe_json_response(
                    self.users_api.get_user(user["id"], host, token)))
        else:
            users = self.users_api.get_all_users(host, token)

        self.multi.start_multi_process_stream(
            self.handle_retrieving_users,
            users,
            processes=processes)

    def handle_retrieving_users(self, user, mongo=None):
        # mongo should be set to None unless this function is being used in a
        # unit test
        if not mongo:
            mongo = MongoConnector()
        user["email"] = user["email"].lower()
        projects_limit = self.config.projects_limit
        if projects_limit:
            user["projects_limit"] = projects_limit

        for key in constants.USER_KEYS_TO_IGNORE:
            user.pop(key, None)
        # SSO causes issues with the avatar URL due to the authentication
        if self.config.group_sso_provider:
            user.pop("avatar_url")
        # Avoid propagating field when creating users on gitlab.com with no config value set
        if is_dot_com(self.config.destination_host) and not projects_limit:
            user.pop("projects_limit")
        mongo.insert_data(
            f"users-{strip_netloc(self.config.source_host)}", user)
        mongo.close_connection()

    def generate_user_data(self, user):
        if user.get("id") is not None:
            user.pop("id")
        if self.config.group_sso_provider is not None:
            return self.generate_user_group_saml_post_data(user)
        user["username"] = self.create_valid_username(user)
        user["skip_confirmation"] = True
        user["reset_password"] = self.config.reset_password
        # make sure the inactive user cannot do anything
        user["force_random_password"] = "true" if user["state"] in self.INACTIVE else self.config.force_random_password
        if not self.config.reset_password and not self.config.force_random_password:
            # TODO: add config for 'password' field
            self.log.warning(
                "If both 'reset_password' and 'force_random_password' are False, the 'password' field has to be set")
        if self.config.dstn_parent_id is not None:
            user["is_admin"] = False
        return user

    def block_user(self, user_data):
        try:
            response = find_user_by_email_comparison_without_id(
                user_data["email"])
            user_creation_data = self.get_user_creation_id_and_email(response)
            if user_creation_data:
                block_response = self.users_api.block_user(
                    self.config.destination_host,
                    self.config.destination_token,
                    user_creation_data["id"])
                self.log.info(
                    f"Blocking user {user_data['username']} email {user_data['email']} (status: {block_response})")
                if isinstance(block_response, Response) and block_response.status_code == 201:
                    self.add_blocked_user_admin_note(user_creation_data)
                else:
                    self.log.error(
                        f"Failed to block user {user_data}, with response:\n{block_response} - {block_response.text}")
                return block_response
        except RequestException as e:
            self.log.error(
                f"Failed request to block user {user_data}, with error:\n{e}")

    def add_blocked_user_admin_note(self, user):
        host = self.config.destination_host
        user_msg = f"blocked user {user['email']}' (ID: {user['id']}) Admin note"
        data = {
            "note": f"User blocked as part of {'GitLab PS' if is_dot_com(host) else ''} user migration from {self.config.source_host}"}
        self.log.info(f"Add {user_msg}")
        try:
            resp = self.users_api.modify_user(
                user["id"], host, self.config.destination_token, data)
            if not isinstance(resp, Response) or resp.status_code != 200:
                self.log.error(
                    f"Failed to add {user_msg}, with response:\n{resp} - {resp.text}")
        except RequestException as e:
            self.log.error(
                f"Failed request to add {user_msg}, with error:\n{e}")

    def handle_user_creation_status(self, response, user):
        """
        Used to handle the user creation response.
        :param response: The response from the create_user attempt
        :param user: The user entity (from staged_users.json) not the user_data that we generate
        :return: The ID of either the created user or the user found by email
        """
        error_resp = f"{response} - {response.text}"
        log_resp = f"User {user} creation failed, due to"
        email = user.get("email")
        if response.status_code == 409:
            self.log.error(f"{log_resp} duplication:\n{error_resp}")
            try:
                # Try to find the user by email. We either just created this,
                # or it already existed
                response = find_user_by_email_comparison_without_id(email)
                return self.get_user_creation_id_and_email(response)
            except RequestException as e:
                self.log.error(
                    f"Failed to retrieve user {user} creation status, due to:\n{e}")
        elif response.status_code == 400:
            return self.log_and_return_failed_user_creation(f"{log_resp} improperly formatted request:\n{error_resp}", email)
        elif response.status_code == 500:
            return self.log_and_return_failed_user_creation(f"{log_resp} internal server error:\n{error_resp}", email)
        else:
            if resp := safe_json_response(response):
                return {
                    "email": resp.get("email"),
                    "id": resp.get("id")
                }
            return self.log_and_return_failed_user_creation(error_resp, email)

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
            if isinstance(response, dict) and response.get("id") is not None:
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
        write_json_to_file(f"{self.app_path}/data/staged_users.json",
                           remove_dupes(staged_users), log=self.log)

    def delete_users(self, dry_run=True, hard_delete=False):
        staged_users = get_staged_users()
        for su in staged_users:
            email = su["email"]
            self.log.info("{0}Removing user {1}".format(
                get_dry_log(dry_run), email))
            user = find_user_by_email_comparison_without_id(email)
            if user is None:
                self.log.info(
                    "User {} does not exist or has already been removed".format(email))
            elif not dry_run:
                try:
                    if get_timedelta(
                            user["created_at"]) < self.config.max_asset_expiration_time:
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

    def set_staged_users_public_email(self, dry_run=True, hide=False):
        staged_users = get_staged_users()
        host = self.config.source_host
        token = self.config.source_token
        if is_gl_version_older_than(14, host, token, "SKIP: Not mandatory to set 'public_email' field for staged users"):
            return
        for su in staged_users:
            # Assume primary email matches on dest
            email = su.get("email")
            su_pub_email = su.get("public_email")
            set_email = su_pub_email if hide else email
            try:
                # Look up user on source
                user = find_user_by_email_comparison_without_id(
                    email, src=True)
                if user:
                    pub_email = user.get("public_email")
                    username = user.get("username")
                else:
                    self.log.warning(
                        f"SKIP: Source user '{email}' NOT found on {host}")
                    continue
                # When to avoid action
                if (hide and not pub_email) or (
                        not hide and pub_email == email):
                    continue
                # When to warn of overwrite
                if not hide and pub_email and pub_email != email:
                    self.log.warning(
                        f"Overwrite source user '{username}' public email '{pub_email}' -> '{email}'")
                self.set_public_email(user.get("id"), set_email, username, host, token, dry_run=dry_run)
            except RequestException as re:
                self.log.error(
                    f"Failed to set source user '{su.get('username')}' public email '{set_email}':\n{re}")
                continue

    def set_public_email(self, uid, email, username, host, token, dry_run=True):
        data = {"public_email": email}
        self.log.info(
            f"{get_dry_log(dry_run)}Set source user '{username}' public email to '{email}'")
        if not dry_run:
            resp = self.users_api.modify_user(uid, host, token, data)
            if not isinstance(resp, Response) or resp.status_code != 200:
                self.log.error(
                    f"Failed to set source user '{username}' public email to '{email}':\n{resp} - {resp.text}")

    def align_user_mapping_emails(self, dry_run=True):
        mapped_users = read_json_file_into_object(f"{self.app_path}/data/user_mapping_by_{self.config.user_mapping_field}.json")
        dry_run_log = get_dry_log(dry_run=dry_run)
        host = self.config.source_host
        token = self.config.source_token
        for m, u in mapped_users.items():
            try:
                dest_primary = u["dest"]["primary"]
                src_public = u["src"]["public"]
                src_id = u["src"]["id"]
                if dest_primary not in u["src"].values() and not dry_run:
                    self.add_user_email(dest_primary, src_id, m, host, token)
                if dest_primary != src_public and not dry_run:
                    self.set_public_email(src_id, dest_primary, m, host, token, dry_run=dry_run)
                else:
                    self.log.info(f"{dry_run_log}User '{m}' mapping emails aligned")
            except RequestException as re:
                self.log.error(
                    f"Failed to align user '{m}' destination '{dest_primary}' primary with source '{src_public}' public email:\n{re}")
            except Exception as e:
                self.log.error(
                    f"Failed to align destination user primary with source user public email:\n{e}")

    def add_user_email(self, email, uid, username, host, token):
        data = {"email": email, "skip_confirmation": True}
        resp = self.users_api.add_user_email(host, token, uid, data)
        if not isinstance(resp, Response) or resp.status_code != 201:
            self.log.error(
                f"Failed to add email '{email}' to source user '{username}' (ID: {uid}):\n{resp} - {resp.text}")
