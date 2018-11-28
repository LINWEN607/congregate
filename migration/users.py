"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import sys
import json
import argparse
import logging
from urllib2 import HTTPError
try:
    from helpers import conf, api, misc_utils
    from helpers import logger as log
except ImportError:
    from congregate.helpers import conf, api, misc_utils
    from congregate.helpers import logger as log

app_path = os.getenv("CONGREGATE_PATH")

l = log.congregate_logger(__name__)

config = conf.ig()

quiet = False

def update_users(obj, new_users, suffix=""):
    unknown_member_indeces = []
    shortcut = {}
    for i in range(len(obj)):
        print "rewriting members for %s" % obj[i]["name"]
        l.logger.info("rewriting members for %s" % obj[i]["name"])
        for ind, member in enumerate(obj[i]["members"], start=0):
            for new_user in new_users:
                key = shortcut.get(member["username"], None)
                saved_id = None
                try:
                    saved_id = key.get("id", None)
                except:
                    saved_id = None
                if saved_id is not None:
                    member["id"] = saved_id
                    break
                elif member["username"] == new_user["username"]:
                    member["id"] = new_user["id"]
                    shortcut[member["username"]] = {"id": new_user["id"]}
                    break
                elif member["username"] + suffix == new_user["username"]:
                    member["id"] = new_user["id"]
                    shortcut[member["username"]] = {"id": new_user["id"]}
                    break
                elif member["name"] == new_user["name"]:
                    member["id"] = new_user["id"]
                    shortcut[member["username"]] = {"id": new_user["id"]}
                    break
                else:
                    old_email = json.load(api.generate_get_request(config.child_host, config.child_token, "users/%d" % member["id"]))["email"]
                    response = json.load(api.generate_get_request(config.parent_host, config.parent_token, "users?search=%s" % old_email))
                    print response
                    if len(response) > 0:
                        member["id"] = response[0]["id"]
                        shortcut[member["username"]] = {"id": response[0]["id"]}
                    else:
                        split_email = old_email.split("@")[0]
                        another_search = json.load(api.generate_get_request(config.parent_host, config.parent_token, "users?search=%s" % split_email))
                        if len(another_search) > 0:
                            member["id"] = another_search[0]["id"]
                            shortcut[member["username"]] = {"id": another_search[0]["id"]}
                        else:
                            print "%s not found" % member["username"]
                            unknown_member_indeces.append(ind)
                    break
        if obj[i].get("namespace", None) is not None:
            if len(obj[i]["members"]) > 0:
                if obj[i]["namespace"] == obj[i]["members"][0]["username"]:
                    new_id = obj[i]["members"][0]["id"]
                    new_namespace = json.load(api.generate_get_request(config.parent_host, config.parent_token, "users/%d" % new_id))["username"]
                    obj[i]["namespace"] = new_namespace
                    print "New namespace for %s: %s" % (obj[i]["members"][0]["username"], new_namespace)
                    shortcut[obj[i]["members"][0]["username"]]["new_namespace"] = new_namespace
                else:
                    search_for_user_namespace = json.load(api.generate_get_request(config.parent_host, config.parent_token, "users/?search=%s" % obj[i]["namespace"]))
                    if len(search_for_user_namespace) > 0:
                        print "Search for namespace: %s" % search_for_user_namespace[0]
                        obj[i]["namespace"] = search_for_user_namespace[0]["username"]
                        if shortcut.get(obj[i]["members"][0]["username"], None) is not None:
                            shortcut[obj[i]["members"][0]["username"]]["new_namespace"] = search_for_user_namespace[0]["username"]
                        else:
                            shortcut[obj[i]["members"][0]["username"]]= {"new_namespace": search_for_user_namespace[0]["username"]}
            else:
                if shortcut.get(obj[i]["namespace"], None) is not None:
                    if shortcut[obj[i]["namespace"]].get("new_namespace", None) is not None:
                        print "Existing namespace for %s: %s" % (obj[i]["namespace"], shortcut[obj[i]["namespace"]].get("new_namespace", None))
                        obj[i]["namespace"] = shortcut[obj[i]["namespace"]].get("new_namespace", None)
                else:
                    search_for_user_namespace = json.load(api.generate_get_request(config.parent_host, config.parent_token, "users/?search=%s" % obj[i]["namespace"]))
                    if len(search_for_user_namespace) > 0:
                        print "Existing namespace for %s: %s" % (obj[i]["namespace"], search_for_user_namespace[0]["username"])
                        if shortcut.get(obj[i]["namespace"], None) is not None:
                            shortcut[obj[i]["namespace"]]["new_namespace"] = search_for_user_namespace[0]["username"]
                        else:
                            shortcut[obj[i]["namespace"]] = {"new_namespace": search_for_user_namespace[0]["username"]}
                        obj[i]["namespace"] = search_for_user_namespace[0]["username"]
                    else:
                        #Super hacky
                        rewritten_namespace = obj[i]["namespace"] + suffix
                        rewritten_namespace = rewritten_namespace.replace("_", ".")
                        print "rewriting %s to %s" % (obj[i]["namespace"], rewritten_namespace)
                        search_for_user_namespace = json.load(api.generate_get_request(config.parent_host, config.parent_token, "users/?search=%s" % rewritten_namespace))
                        if len(search_for_user_namespace) > 0:
                            print "Existing namespace for %s: %s" % (obj[i]["namespace"], search_for_user_namespace[0]["username"])
                            if shortcut.get(obj[i]["namespace"], None) is not None:
                                shortcut[obj[i]["namespace"]]["new_namespace"] = search_for_user_namespace[0]["username"]
                            else:
                                shortcut[obj[i]["namespace"]]= {"new_namespace": search_for_user_namespace[0]["username"]}
                            obj[i]["namespace"] = search_for_user_namespace[0]["username"]

        if len(unknown_member_indeces) > 0:
            print unknown_member_indeces
            for index in range(len(unknown_member_indeces), 0, -1):
                print index
                print "Index %s" % str(unknown_member_indeces)
                print json.dumps(obj[i]["members"], indent=4)
                del obj[i]["members"][unknown_member_indeces[index-1]]
            unknown_member_indeces = []
                    
    return obj

def update_users_new(obj, new_users):
    
    rewritten_users = {}
    for i in range(len(new_users)):
        new_obj = new_users[i]
        id_num = new_users[i]["email"]
        rewritten_users[id_num] = new_obj
    
    for i in range(len(obj)):
        l.logger.info("Rewriting users for %s" % obj[i]["name"])
        members = obj[i]["members"]
        for member in members:
            old_email = json.load(api.generate_get_request(config.child_host, config.child_token, "users/%d" % member["id"]))["email"]
            if rewritten_users.get(old_email, None) is not None:
                member["id"] = rewritten_users[old_email]["id"]
    
    return obj

    

def update_user_info_separately():
    with open("%s/data/stage.json" % app_path, "r") as f:
        staged_projects = json.load(f)

    with open("%s/data/staged_groups.json" % app_path, "r") as f:
        groups = json.load(f)

    with open("%s/data/new_users.json" % app_path, "r") as f:
        new_users = json.load(f)

    staged_projects = update_users(staged_projects, new_users)
    groups = update_users(groups, new_users)


    with open("%s/data/stage.json" % app_path, "wb") as f:
        json.dump(staged_projects, f, indent=4)
    
    with open("%s/data/staged_groups.json" % app_path, "wb") as f:
        json.dump(groups, f, indent=4)

def add_users_to_parent_group():
    with open("%s/data/newer_users.json" % app_path, "r") as f:
        new_users = json.load(f)
    
    for user in new_users:
        data = {
            "user_id": user["id"],
            "access_level": 10
        }
        try:
            print "Adding %s to group" % user["username"]
            api.generate_post_request(config.parent_host, config.parent_token, "groups/%d/members" % config.parent_id, json.dumps(data))
        except HTTPError, e:
            l.logger.error(e)

def remove_users_from_parent_group():
    count = 0
    users = api.list_all(config.parent_host, config.parent_token, "groups/%d/members" % config.parent_id)
    for user in users:
        if user["access_level"] <= 20:
            count += 1
            api.generate_delete_request(config.parent_host, config.parent_token, "/groups/%d/members/%d" % (config.parent_id, user["id"]))
        else:
            print "Keeping this user"
            print user
    print count

def lower_user_permissions():
    all_users = list(api.list_all(config.parent_host, config.parent_token, "groups/%d/members" % config.parent_id))
    for user in all_users:
        if user["access_level"] == 20:
            l.logger.info("Lowering %s's access level to guest" % user["username"])
            response = api.generate_put_request(config.parent_host, config.parent_token, "groups/%d/members/%d?access_level=10" % (config.parent_id, user["id"]), data=None)
            print response
        else:
            l.logger.info("Not changing %s's access level" % user["username"])

def remove_blocked_users():
    count = 0
    with open("%s/data/new_users.json" % app_path, "r") as f:
        new_users = json.load(f)
    with open("%s/data/users.json" % app_path, "r") as f:
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

    with open("%s/data/newer_users.json" % app_path, "wb") as f:
        json.dump(newer_users, f, indent=4)
    

def update_user_info(new_ids, overwrite=True):
    if overwrite:
        with open("%s/data/new_users.json" % app_path, "w") as f:
            new_users = []
            for new_id in new_ids:
                new_user = json.load(api.generate_get_request(config.parent_host, config.parent_token, "/users/%s" % new_id))[0]
                new_users.append(new_user)
            
            root_index = None
            for user in new_users:
                if user["id"] == 1:
                    root_index = new_users.index(user)
                    break
            if root_index:
                new_users.pop(root_index)
            
            json.dump(new_users, f, indent=4)

    with open("%s/data/stage.json" % app_path, "r") as f:
        staged_projects = json.load(f)

    with open("%s/data/staged_groups.json" % app_path, "r") as f:
        groups = json.load(f)

    with open("%s/data/new_users.json" % app_path, "r") as f:
        new_users = json.load(f)

    staged_projects = update_users(staged_projects, new_users, None)
    groups = update_users(groups, new_users, None)
        
    with open("%s/data/stage.json" % app_path, "wb") as f:
        json.dump(staged_projects, f, indent=4)
    
    with open("%s/data/staged_groups.json" % app_path, "wb") as f:
        json.dump(groups, f, indent=4)

def update_user_after_migration():
    with open("%s/data/staged_users.json" % app_path, "r") as f:
        users = json.load(f)
    new_users = []
    users_not_found = []
    for user in users:
        print "searching for %s" % user["email"]
        new_user = api.generate_get_request(config.parent_host, config.parent_token, "users?search=%s" % user["email"])
        response = json.load(new_user)
        print response
        if len(response) > 0:
            new_users.append(response[0])
        else:
            print "searching for %s" % user["username"]
            new_user = api.generate_get_request(config.parent_host, config.parent_token, "users?search=%s" % user["username"])
            response2 = json.load(new_user)
            if len(response2) > 0:
                new_users.append(response[0])
            else: 
                users_not_found.append(user["email"])
                print response
            
    other_ids = []
    if os.path.isfile("%s/data/ids.txt" % app_path):
        with open("%s/data/ids.txt" % app_path, "r") as f:
            for line in f.readlines():
                other_ids.append(line)

    for other_id in other_ids:
        print "searching for %s" % other_id
        new_user = api.generate_get_request(config.parent_host, config.parent_token, "users/%s" % other_id)
        response = json.load(new_user)
        new_users.append(response)

    with open("%s/data/new_users.json" % app_path, "w") as f:
        json.dump(new_users, f, indent=4)
    with open("%s/data/users_not_found.json" % app_path, "w") as f:
        json.dump(users_not_found, f, indent=4)

    print len(new_users)

def retrieve_user_info(quiet=False):
    users = list(api.list_all(config.child_host, config.child_token, "users"))
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

    with open('%s/data/users.json' % app_path, "w") as f:
        json.dump(users, f, indent=4)
    
    if not quiet:
        l.logger.info("Retrieved %d users. Check users.json to see all retrieved groups" % len(users))

def migrate_user_info():
    new_ids = []
    with open('%s/data/staged_users.json' % app_path, "r") as f:
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
            response = api.generate_post_request(config.parent_host, config.parent_token, "users", json.dumps(user))
            response_json = json.load(response)
            print response_json
            new_ids.append(response_json["id"])
        except HTTPError, e:
            if e.code == 409:
                l.logger.info("User already exists")
                try:
                    l.logger.info("Appending %s to new_users.json" % user["email"])
                    response = api.generate_get_request(config.parent_host, config.parent_token, "users?search=%s" % user["email"])
                    new_ids.append(json.load(response)[0]["id"])
                except HTTPError, e:
                    l.logger.info(e)
                    l.logger.info(e.read())
            l.logger.info(e)

    return new_ids
    

def append_users(users):
    with open("%s/data/users.json" % app_path, "r") as f:
        user_file = json.load(f)
    staged_users = []
    for user in users:
        for u in user_file:
            if user == u["username"]:
                staged_users.append(u)
                l.logger.info("Staging user (%s) [%d/%d]" % (u["username"], len(staged_users), len(users)))
    with open("%s/data/staged_users.json" % app_path, "w") as f:
        json.dump(misc_utils.remove_dupes(staged_users), f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle user-related tasks')
    parser.add_argument('--retrieve', type=bool, default=False, dest='retrieve',
                    help='Retrieve user info and save it to %s/data/users.json' % app_path)
    parser.add_argument('--migrate', type=bool, default=False, dest='migrate',
                    help='Migrate all user info to parent instance')
    parser.add_argument('--update', type=bool, default=False, dest='update',
                    help='Update all project/group users info to parent instance')
    parser.add_argument('--quiet', type=bool, default=False, dest='quiet',
                    help='Silent output of script')

    args = parser.parse_args()

    retrieve = args.retrieve
    migrate = args.migrate
    update = args.update
    quiet = args.quiet

    if retrieve:
        retrieve_user_info()
    if migrate:
        migrate_user_info()
    if update:
        # TODO: fix this
        print "update through the UI"
        #update_user_info()

