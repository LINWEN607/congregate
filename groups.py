"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import urllib
import urllib2
import json
import sys
import subprocess
import argparse

app_path = os.getenv("CONGREGATE_PATH")

def generate_post_response(host, token, api, data):
    url = "%s/api/v4/groups/%s" % (host, api)
    headers = {
        'Private-Token': token
    }
    req = urllib2.Request(url, headers=headers, data=data)
    response = urllib2.urlopen(req)
    return response

def generate_get_response(host, token, api):
    url = "%s/api/v4/%s" % (host, api)
    headers = {
        'Private-Token': token
    }
    req = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(req)
    return response

def retrieve_group_info():
    groups = json.load(generate_get_response(child_host, child_token, "groups"))

    for group in groups:
        group.pop("web_url")
        group.pop("full_name")
        group.pop("full_path")
        group.pop("ldap_cn")
        group.pop("ldap_access")
        members = json.load(generate_get_response(child_host, child_token, "groups/%s/members" % str(group["id"])))
        group["members"] = members
        group.pop("id")

    with open('%s/data/groups.json' % app_path, "w") as f:
        json.dump(groups, f, indent=4)

def migrate_group_info():
    if not os.path.isfile("%s/data/groups.json" % app_path):
        retrieve_group_info()
    with open("%s/data/groups.json" % app_path, "r") as f:
        groups = json.loads(f)
    
    for group in groups:
        members = group["members"]
        group.pop("members")
        generate_post_response(parent_host, parent_token, "groups", group)
        new_group = generate_get_response(parent_host, parent_token, "groups?search=%s" % group["name"])
        if new_group[0]["name"] == group["name"]:
            for member in members:
                new_member = {
                    "user_id": member["id"],
                    "access_level": member["access_level"]
                }
                generate_post_response(parent_host, parent_token, "groups/%d/members" % new_group[0]["id"], new_member)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle group-related tasks')
    parser.add_argument('--retrieve', type=bool, default=False, dest='retrieve',
                    help='Retrieve group info and save it to %s/data/groups.json' % app_path)
    parser.add_argument('--migrate', type=bool, default=False, dest='migrate',
                    help='Migrate all group info to parent instance')

    args = parser.parse_args()

    retrieve = args.retrieve
    migrate = args.migrate

    with open('%s/data/config.json' % app_path) as f:
        config = json.load(f)["config"]

    child_host = config["child_instance_host"]
    child_token = config["child_instance_token"]
    parent_host = config["parent_instance_host"]
    parent_token = config["parent_instance_token"]

    if retrieve:
        retrieve_group_info()
