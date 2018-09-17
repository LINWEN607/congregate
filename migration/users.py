"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import sys
import json
import argparse
from helpers import api, conf

app_path = os.getenv("CONGREGATE_PATH")

with open('%s/data/config.json' % app_path) as f:
        config = json.load(f)["config"]

child_host = config["child_instance_host"]
child_token = config["child_instance_token"]
parent_host = config["parent_instance_host"]
parent_token = config["parent_instance_token"]
quiet = False

def update_users(obj, new_users):
    for i in range(len(obj)):
        for member in obj[i]["members"]:
            for new_user in new_users:
                if member["username"] == new_user["username"]:
                    member["id"] = new_user["id"]
    return obj

def update_user_info():
    with open("%s/data/new_users.json" % app_path, "w") as f:
        new_users = json.load(api.generate_get_request(parent_host, parent_token, "users"))
        
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

    staged_projects = update_users(staged_projects, new_users)
    groups = update_users(groups, new_users)
        
    with open("%s/data/stage.json" % app_path, "wb") as f:
        json.dump(staged_projects, f, indent=4)
    
    with open("%s/data/staged_groups.json" % app_path, "wb") as f:
        json.dump(groups, f, indent=4)

def retrieve_user_info(quiet=False):
    users = list(api.list_all(child_host, child_token, "users"))
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
                "id",
                "state"
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
        print "Retrieved %d users. Check users.json to see all retrieved groups" % len(users)

def migrate_user_info():
    with open('%s/data/staged_users.json' % app_path, "r") as f:
        users = json.load(f)
    
    for user in users:
        api.generate_post_request(parent_host, parent_token, "users", json.dumps(user))

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
        update_user_info()

