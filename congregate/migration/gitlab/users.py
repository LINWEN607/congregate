from helpers.base_class import BaseClass
from helpers import api
from helpers.misc_utils import strip_numbers, remove_dupes
from migration.gitlab.groups import GroupsClient
from requests.exceptions import RequestException
from os import path
import json


class UsersClient(BaseClass):
    def __init__(self):
        self.groups = GroupsClient()
        super(UsersClient, self).__init__()

    def get_user(self, id, host, token):
        return api.generate_get_request(host, token, "users/%d" % id)

    def get_current_user(self, host, token):
        return api.generate_get_request(host, token, "user")

    def create_user(self, host, token, data):
        return api.generate_post_request(host, token, "users", json.dumps(data))

    def update_users(self, obj, new_users):
        rewritten_users = {}
        for i in range(len(new_users)):
            new_obj = new_users[i]
            username = strip_numbers(new_users[i]["username"]).lower()
            rewritten_users[username] = new_obj

        for i in range(len(obj)):
            self.log.info("Rewriting users for %s" % obj[i]["name"])
            members = obj[i]["members"]
            if isinstance(members, list):
                for member in members:
                    self.log.info(member)
                    username = strip_numbers(member["username"]).lower()
                    if rewritten_users.get(member["username"], None) is not None:
                        member["id"] = rewritten_users[username]["id"]
                    elif rewritten_users.get(member["name"].replace(" ", ".").lower(), None) is not None:
                        member["id"] = rewritten_users[member["name"].replace(
                            " ", ".").lower()]["id"]
                    else:
                        member["id"] = self.config.parent_user_id
                    # else:
                    #     old_username = api.generate_get_request(self.config.child_host, self.config.child_token, "users/%d" % member["id"]).json()["username"]
                    #     old_username = misc_utils.strip_numbers(old_username)
                    #     if rewritten_users.get(old_username, None) is not None:

                    #         member["id"] = rewritten_users[old_username]["id"]

        return obj

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
                    self.config.parent_id, self.config.parent_host, self.config.parent_token, data)
            except RequestException, e:
                self.log.error(e)

    def remove_users_from_parent_group(self):
        count = 0
        users = api.list_all(self.config.parent_host, self.config.parent_token,
                             "groups/%d/members" % self.config.parent_id)
        for user in users:
            if user["access_level"] <= 20:
                count += 1
                api.generate_delete_request(self.config.parent_host, self.config.parent_token,
                                            "/groups/%d/members/%d" % (self.config.parent_id, user["id"]))
            else:
                print "Keeping this user"
                print user
        print count

    def lower_user_permissions(self):
        all_users = list(api.list_all(self.config.parent_host,
                                      self.config.parent_token, "groups/%d/members" % self.config.parent_id))
        for user in all_users:
            if user["access_level"] == 20:
                self.log.info("Lowering %s's access level to guest" %
                              user["username"])
                response = api.generate_put_request(self.config.parent_host, self.config.parent_token,
                                                    "groups/%d/members/%d?access_level=10" % (self.config.parent_id, user["id"]), data=None)
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
                    #print "Need to remove %s" % new_user["username"]
                    count += 1
                else:
                    newer_users.append(new_user)
            else:
                key = new_user["name"]
                if rewritten_users_by_name.get(key, None) is not None:
                    if rewritten_users_by_name[key]["state"] == "blocked":
                        #print "Need to remove %s" % new_user["name"]
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
                    new_user = self.get_user(
                        new_id, self.config.parent_host, self.config.parent_token).json()
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
            print "searching for %s" % user["email"]
            new_user = api.search(
                self.config.parent_host, self.config.parent_token, 'users', user['email'])
            print new_user
            if len(new_user) > 0:
                new_users.append(new_user[0])
            else:
                print "searching for %s" % user["username"]
                new_user2 = api.search(
                    self.config.parent_host, self.config.parent_token, 'users', user['username'])
                if len(new_user2) > 0:
                    new_users.append(new_user2[0])
                else:
                    users_not_found.append(user["email"])
                    print new_user

        other_ids = []
        if path.isfile("%s/data/ids.txt" % self.app_path):
            with open("%s/data/ids.txt" % self.app_path, "r") as f:
                for line in f.readlines():
                    other_ids.append(line)

        for other_id in other_ids:
            print "searching for %s" % other_id
            new_user = self.get_user(
                other_id, self.config.parent_host, self.config.parent_token).json()
            new_users.append(new_user)

        with open("%s/data/new_users.json" % self.app_path, "w") as f:
            json.dump(new_users, f, indent=4)
        with open("%s/data/users_not_found.json" % self.app_path, "w") as f:
            json.dump(users_not_found, f, indent=4)

        print len(new_users)

    def retrieve_user_info(self, quiet=False):
        users = list(api.list_all(self.config.child_host,
                                  self.config.child_token, "users"))
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
        for user in users:
            try:
                user["username"] = user["username"]
                user["skip_confirmation"] = True
                # if user.get("identities", None) is not None:
                #     user["extern_uid"] = user["identities"][0]["extern_uid"]
                #     user["provider"] = user["identities"][0]["provider"]
                #     user.pop("identities")
                # print json.dumps(user, indent=4)
                response = self.create_user(
                    self.config.parent_host, self.config.parent_token, user)
                print response

                if response.status_code == 409:
                    self.log.info("User already exists")

                    try:
                        self.log.info(
                            "Appending %s to new_users.json" % user["email"])
                        response = api.search(
                            self.config.parent_host, self.config.parent_token, 'users', user['email'])
                        if len(response) > 0:
                            if isinstance(response, list):
                                new_ids.append(response[0]["id"])
                            elif isinstance(response, dict):
                                if response.get("id", None) is not None:
                                    new_ids.append(response["id"])
                    except RequestException, e:
                        self.log.info(e)
                else:
                    new_ids.append(response.json()["id"])
            except RequestException, e:
                self.log.info(e)

        return new_ids

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
