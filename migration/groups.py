"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import json
import sys
import subprocess
import argparse
import urllib2
try:
    from helpers import conf, api
except ImportError:
    from congregate.helpers import conf, api

app_path = os.getenv("CONGREGATE_PATH")

with open('%s/data/config.json' % app_path) as f:
    config = json.load(f)["config"]

child_host = config["child_instance_host"]
child_token = config["child_instance_token"]
parent_host = config["parent_instance_host"]
parent_token = config["parent_instance_token"]

def retrieve_group_info(quiet=False):
    groups = list(api.list_all(child_host, child_token, "groups"))

    for group in groups:
        group.pop("web_url")
        group.pop("full_name")
        group.pop("full_path")
        group.pop("ldap_cn")
        group.pop("ldap_access")
        members = json.load(api.generate_get_request(child_host, child_token, "groups/%s/members" % str(group["id"])))
        group["members"] = members
        group.pop("id")

    with open('%s/data/groups.json' % app_path, "w") as f:
        json.dump(groups, f, indent=4)
    
    if not quiet:
        print "Retrieved %d groups. Check groups.json to see all retrieved groups" % len(groups)

def migrate_group_info():
    if not os.path.isfile("%s/data/groups.json" % app_path):
        retrieve_group_info()
    with open("%s/data/staged_groups.json" % app_path, "r") as f:
        groups = json.load(f)
    
    for group in groups:
        members = group["members"]
        group.pop("members")
        try:
            api.generate_post_request(parent_host, parent_token, "groups", json.dumps(group))
        except urllib2.HTTPError, e:
            print "Group already exists"
        new_group = json.load(api.generate_get_request(parent_host, parent_token, "groups?search=%s" % group["name"]))

        if new_group[0]["name"] == group["name"]:
            root_user_present = False
            for member in members:
                if member["id"] == 1:
                    root_user_present = True
                new_member = {
                    "user_id": member["id"],
                    "access_level": member["access_level"]
                }

                try:
                    api.generate_post_request(parent_host, parent_token, "groups/%d/members" % new_group[0]["id"], json.dumps(new_member))
                except urllib2.HTTPError, e:
                    print e

            if not root_user_present:
                print "removing root user from group"
                api.generate_delete_request(parent_host, parent_token, "/groups/%d/members/1" % new_group[0]["id"])

def append_groups(groups):
    with open("%s/data/groups.json" % app_path, "r") as f:
        group_file = json.load(f)
    with open("%s/data/staged_groups.json" % app_path, "r") as f:
        staged_groups = json.load(f)
    for group in groups:
        for g in group_file:
            if group == g["path"]:
                staged_groups.append(g)
    with open("%s/data/staged_groups.json" % app_path, "w") as f:
        json.dump(staged_groups, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle group-related tasks')
    parser.add_argument('--retrieve', type=bool, default=False, dest='retrieve',
                    help='Retrieve group info and save it to %s/data/groups.json' % app_path)
    parser.add_argument('--migrate', type=bool, default=False, dest='migrate',
                    help='Migrate all group info to parent instance')
    parser.add_argument('--quiet', type=bool, default=False, dest='quiet',
                    help='Silent output of script')

    args = parser.parse_args()

    retrieve = args.retrieve
    migrate = args.migrate
    quiet = args.quiet

    if retrieve:
        retrieve_group_info()
    
    if migrate:
        migrate_group_info()
