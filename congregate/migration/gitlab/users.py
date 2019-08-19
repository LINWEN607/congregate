from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.helpers.threads import handle_multi_thread
from congregate.helpers.misc_utils import strip_numbers, remove_dupes
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.users import UsersApi
from requests.exceptions import RequestException
from os import path
import json


class UsersClient(BaseClass):
    def __init__(self):
        self.groups = GroupsApi()
        self.users = UsersApi()
        super(UsersClient, self).__init__()

    def find_user_by_email_comparison_with_id(self, old_user_id):
        self.log.info("Searching for old user {0} by id".format(old_user_id))
        old_user = self.users.get_user(
            old_user_id,
            self.config.source_host,
            self.config.source_token).json()
        self.log.info("Found old user by id {0}".format(old_user))
        if old_user is not None and old_user and old_user.get("email", None) is not None:
            return self.find_user_by_email_comparison_without_id(old_user["email"])
        return None

    def find_user_by_email_comparison_without_id(self, email):
        self.log.info("Searching for old user {0} by email".format(email))
        users = self.users.search_for_user_by_email(
            self.config.destination_host,
            self.config.destination_token,
            email)
        for user in users:
            self.log.info(user)
            if user is not None and user and user.get("email", None) is not None and user["email"] == email:
                self.log.info("Found old user by email {0}".format(user))
                return user
        return None

    def username_exists(self, old_user):
        index = 0
        username = old_user["username"]
        for user in self.users.search_for_user_by_email(self.config.destination_host, self.config.destination_token,
                                                        username):
            if user["username"] == username:
                return True
            elif index > 100:
                return False
            index += 1
        return False

    def user_email_exists(self, old_user):
        index = 0
        email = old_user["email"]
        for user in self.users.search_for_user_by_email(self.config.destination_host, self.config.destination_token,
                                                        email):
            if user["email"] == email:
                return True
            elif index > 100:
                return False
            index += 1
        return False

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
            new_impersonation_token = self.users.create_user_impersonation_token(
                self.config.destination_host, self.config.destination_token, id, data).json()
            users_map[email] = new_impersonation_token
            users_map[email]["user_id"] = id
        return users_map[email]

    def delete_saved_impersonation_tokens(self, users_map):
        for user in users_map.values():
            self.users.delete_user_impersonation_token(
                self.config.destination_host, self.config.destination_token, user["user_id"], user["id"])

    def generate_user_group_saml_post_data(self, user):
        identities = user.pop("identities")
        user["external"] = True
        user["group_id_for_saml"] = self.config.parent_id
        user["extern_uid"] = self.find_extern_uid_by_provider(identities, self.config.group_sso_provider)
        user["provider"] = "group_saml"
        user["reset_password"] = True
        user["skip_confirmation"] = True
        user["username"] = self.create_valid_username(user)

        return user

    def find_extern_uid_by_provider(self, identities, provider):
        for identity in identities:
            if provider == identity["provider"]:
                return identity["extern_uid"]

    def create_valid_username(self, user):
        username = user["username"]
        if not self.user_email_exists(user):
            if self.username_exists(user):
                if self.config.username_suffix is not None:
                    return "%s_%s" % (username, self.config.username_suffix)
                else:
                    self.log.error("Username suffix not set. Defaulting to a single underscore following the username")
                    return "%s_" % (username)
        return username

    def update_users(self, obj, new_users):
        rewritten_users = {}
        for i in range(len(new_users)):
            new_obj = new_users[i]
            username = strip_numbers(new_users[i]["email"]).lower()
            rewritten_users[username] = new_obj

        for i in range(len(obj)):
            self.log.info("Rewriting users for %s" % obj[i]["name"])
            members = obj[i]["members"]
            if isinstance(members, list):
                for member in members:
                    old_user = self.users.get_user(member["id"], self.config.source_host, self.config.source_token)
                    old_user = old_user.json()
                    username = strip_numbers(member["username"]).lower()
                    if rewritten_users.get(old_user["email"], None) is not None:
                        new_user = self.users.get_user(rewritten_users[old_user["email"]]["id"],
                                                       self.config.destination_host,
                                                       self.config.destination_token).json()
                        if new_user.get("message", None) is None:
                            if new_user["email"] == old_user["email"]:
                                member["id"] = rewritten_users[old_user["email"]]["id"]
                            else:
                                member["id"] = self.config.import_user_id
                        else:
                            member["id"] = self.config.import_user_id
                    else:
                        member["id"] = self.config.import_user_id

        return obj

    def map_new_users_to_groups_and_projects(self, dry_run = False):
        not_found_users = []
        user_found = False
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

        for p in staged_projects:
            # Over every project, check the members
            if p.get("members", None) is not None and p["members"]:
                for m in p["members"]:
                    username = m["username"]
                    # Find the match in new_users.json
                    for u in new_users:
                        if u["username"] == username or u["username"] == username + self.config.username_suffix:
                            m["id"] = u["id"]
                            user_found = True
                            break
                    if not user_found:
                        not_found_users.append((username, "(project: " + p["namespace"] + ")"))
                    user_found = False

        user_found = False

        for g in staged_groups:
            # Over every project, check the members
            if g.get("members", None) is not None and g["members"]:
                for m in g["members"]:
                    username = m["username"]
                    # Find the match in new_users.json
                    for u in new_users:
                        if u["username"] == username or u["username"] == username + self.config.username_suffix:
                            m["id"] = u["id"]
                            user_found = True
                            break
                    if not user_found:
                        not_found_users.append((username, "(group: " + g["full_path"] + ")"))
                    user_found = False

        self.log.info("Following users were not found:\n{}".format("\n".join(" ".join(u) for u in not_found_users)))

        if not dry_run:
            self.log.info("Mapping users to projects and groups.")
            with open("%s/data/stage.json" % self.app_path, "wb") as f:
                json.dump(staged_projects, f, indent=4)

            with open("%s/data/staged_groups.json" % self.app_path, "wb") as f:
                json.dump(staged_groups, f, indent=4)

    def update_user_info_separately(self):
        with open("%s/data/stage.json" % self.app_path, "r") as f:
            staged_projects = json.load(f)

        with open("%s/data/staged_groups.json" % self.app_path, "r") as f:
            groups = json.load(f)

        with open("%s/data/new_users.json" % self.app_path, "r") as f:
            new_users = json.load(f)

        staged_projects = self.update_users(staged_projects, new_users)
        groups = self.update_users(groups, new_users)

        with open("%s/data/stage.json" % self.app_path, "wb") as f:
            json.dump(staged_projects, f, indent=4)

        with open("%s/data/staged_groups.json" % self.app_path, "wb") as f:
            json.dump(groups, f, indent=4)

    def add_users_to_parent_group(self):
        with open("%s/data/newer_users.json" % self.app_path, "r") as f:
            new_users = json.load(f)

        for user in new_users:
            data = {
                "user_id": user["id"],
                "access_level": 10
            }
            try:
                print "Adding %s to group" % user["username"]
                self.groups.add_member_to_group(
                    self.config.parent_id, self.config.destination_host, self.config.destination_token, data)
            except RequestException, e:
                self.log.error(e)

    def remove_users_from_parent_group(self):
        count = 0
        users = api.list_all(self.config.destination_host, self.config.destination_token,
                             "groups/%d/members" % self.config.parent_id)
        for user in users:
            if user["access_level"] <= 20:
                count += 1
                api.generate_delete_request(self.config.destination_host, self.config.destination_token,
                                            "/groups/%d/members/%d" % (self.config.parent_id, user["id"]))
            else:
                print "Keeping this user"
                print user
        print count

    def lower_user_permissions(self):
        all_users = list(api.list_all(self.config.destination_host,
                                      self.config.destination_token, "groups/%d/members" % self.config.parent_id))
        for user in all_users:
            if user["access_level"] == 20:
                self.log.info("Lowering %s's access level to guest" %
                              user["username"])
                response = api.generate_put_request(self.config.destination_host, self.config.destination_token,
                                                    "groups/%d/members/%d?access_level=10" % (
                                                    self.config.parent_id, user["id"]), data=None)
                print response
            else:
                self.log.info("Not changing %s's access level" %
                              user["username"])

    def remove_blocked_users(self):
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
                    # print "Need to remove %s" % new_user["username"]
                    count += 1
                else:
                    newer_users.append(new_user)
            else:
                key = new_user["name"]
                if rewritten_users_by_name.get(key, None) is not None:
                    if rewritten_users_by_name[key]["state"] == "blocked":
                        # print "Need to remove %s" % new_user["name"]
                        count += 1
                    else:
                        newer_users.append(new_user)
        print "newer user count: %d" % len(newer_users)
        print "Need to remove %d users" % count

        with open("%s/data/newer_users.json" % self.app_path, "wb") as f:
            json.dump(newer_users, f, indent=4)

    def update_user_info(self, new_ids, overwrite=True):
        if overwrite:
            with open("%s/data/new_users.json" % self.app_path, "w") as f:
                new_users = []
                for new_id in new_ids:
                    new_user = self.users.get_user(
                        new_id, self.config.destination_host, self.config.destination_token).json()
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
            groups = json.load(f)

        with open("%s/data/new_users.json" % self.app_path, "r") as f:
            new_users = json.load(f)

        staged_projects = self.update_users(staged_projects, new_users)
        groups = self.update_users(groups, new_users)

        with open("%s/data/stage.json" % self.app_path, "wb") as f:
            json.dump(staged_projects, f, indent=4)

        with open("%s/data/staged_groups.json" % self.app_path, "wb") as f:
            json.dump(groups, f, indent=4)

    def update_user_after_migration(self):
        with open("%s/data/staged_users.json" % self.app_path, "r") as f:
            users = json.load(f)
        new_users = []
        users_not_found = []
        for user in users:
            self.log.info("Searching for user {} (email)".format(user["email"]))
            new_user = api.search(
                self.config.destination_host, self.config.destination_token, 'users', user['email'])
            if len(new_user) > 0:
                if new_user[0].get("email", None) is None:
                    new_user[0]["email"] = user["email"]
                new_users.append(new_user[0])
            else:
                self.log.info("Searching for user {} (username)".format(user["username"]))
                new_user2 = api.search(
                    self.config.destination_host, self.config.destination_token, 'users', user['username'])
                if len(new_user2) > 0:
                    new_users.append(new_user2[0])
                else:
                    users_not_found.append(user["email"])

        other_ids = []
        if path.isfile("%s/data/ids.txt" % self.app_path):
            with open("%s/data/ids.txt" % self.app_path, "r") as f:
                for line in f.readlines():
                    other_ids.append(line)

        for other_id in other_ids:
            self.log.info("Searching for user {} (ID)".format(other_id))
            new_user = self.users.get_user(
                other_id, self.config.destination_host, self.config.destination_token).json()
            new_users.append(new_user)

        with open("%s/data/new_users.json" % self.app_path, "w") as f:
            json.dump(new_users, f, indent=4)
        with open("%s/data/users_not_found.json" % self.app_path, "w") as f:
            json.dump(users_not_found, f, indent=4)

        self.log.info("New users ({}):\n{}".format(len(new_users), "\n".join(u["email"] for u in new_users)))

    def retrieve_user_info(self, quiet=False):
        users = list(api.list_all(self.config.source_host,
                                  self.config.source_token, "users"))
        root_index = None
        for user in users:
            # Removing root user
            if user["id"] == 1:
                root_index = users.index(user)
            else:
                keys_to_delete = [
                    "web_url",
                    "last_sign_in_at",
                    "last_activity_at",
                    "current_sign_in_at",
                    "can_create_project",
                    "two_factor_enabled",
                    "avatar_url",
                    "created_at",
                    "confirmed_at",
                    "last_activity_on",
                    "id"
                ]
                for key in keys_to_delete:
                    if key in user:
                        user.pop(key)
                user["reset_password"] = True

        if root_index:
            users.pop(root_index)

        with open('%s/data/users.json' % self.app_path, "w") as f:
            json.dump(users, f, indent=4)

        if not quiet:
            self.log.info(
                "Retrieved %d users. Check users.json to see all retrieved groups" % len(users))

    def migrate_user_info(self):
        new_ids = []
        with open('%s/data/staged_users.json' % self.app_path, "r") as f:
            users = json.load(f)

        new_ids = handle_multi_thread(self.handle_user_creation, users)
        return list(filter(None, new_ids))

    def user_migration_dry_run(self):
        self.log.info("Running a dry run user migration. This will output the various POST data you will send.")
        with open('%s/data/staged_users.json' % self.app_path, "r") as f:
            users = json.load(f)
        post_data = handle_multi_thread(self.generate_user_data, users)

        with open('%s/data/dry_run_user_migration.json' % self.app_path, "w") as f:
            self.log.info("Writing data to dry_run_user_migration.json")
            json.dump(post_data, f, indent=4)

    def generate_user_data(self, user):
        if self.config.group_sso_provider is not None:
            return self.generate_user_group_saml_post_data(user)
        else:
            user["username"] = self.create_valid_username(user)
            user["skip_confirmation"] = True
            return user

    def handle_user_creation(self, user):
        user_data = self.generate_user_data(user)
        try:
            response = self.users.create_user(
                self.config.destination_host, self.config.destination_token, user_data)
        except RequestException, e:
            self.log.info(e)
            response = None

        if response is not None:
            return self.handle_user_creation_status(response, user)
        return None

    def handle_user_creation_status(self, response, user):
        if response.status_code == 409:
            self.log.info("User already exists")
            try:
                self.log.info(
                    "Appending %s to new_users.json" % user["email"])
                response = self.find_user_by_email_comparison_without_id(user["email"])
                if len(response) > 0:
                    if isinstance(response, list):
                        return response[0]["id"]
                    elif isinstance(response, dict):
                        if response.get("id", None) is not None:
                            return response["id"]
            except RequestException, e:
                self.log.info(e)
        else:
            return response.json()["id"]

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
