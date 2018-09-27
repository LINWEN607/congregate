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
import logging
try:
    from helpers import conf, api, misc_utils
except ImportError:
    from congregate.helpers import conf, api, misc_utils

app_path = os.getenv("CONGREGATE_PATH")
logging.getLogger(__name__)
config = conf.ig()

def traverse_groups(base_groups, transient_list, parent_group=None):
    if parent_group is not None:
        parent_group["child_ids"] = []
    for group in base_groups:
        group.pop("web_url")
        group.pop("full_name")
        group.pop("full_path")
        group.pop("ldap_cn")
        group.pop("ldap_access")
        members = json.load(api.generate_get_request(config.child_host, config.child_token, "groups/%s/members" % str(group["id"])))
        group["members"] = members
        transient_list.append(group)
        subgroups = json.load(api.generate_get_request(config.child_host, config.child_token, "groups/%s/subgroups" % str(group["id"])))
        if parent_group is not None:
            parent_group["child_ids"].append(group["id"])
        if len(subgroups) > 0:
            parent_group = transient_list[-1]
            logging.info("traversing into a subgroup")
            traverse_groups(subgroups, transient_list, parent_group)
        else:
            logging.info("No subgroups found")
        parent_group = None
            

def retrieve_group_info(quiet=False):
    groups = list(api.list_all(config.child_host, config.child_token, "groups"))
    transient_list = []

    traverse_groups(groups, transient_list)

    with open('%s/data/groups.json' % app_path, "w") as f:
        json.dump(groups, f, indent=4)
    
    if not quiet:
        logging.info("Retrieved %d groups. Check groups.json to see all retrieved groups" % len(groups))

def migrate_group_info():
    if not os.path.isfile("%s/data/groups.json" % app_path):
        retrieve_group_info()
    with open("%s/data/staged_groups.json" % app_path, "r") as f:
        groups = json.load(f)

    rewritten_groups = {}
    for i in range(len(groups)):
        new_obj = groups[i]
        group_name = groups[i]["id"]
        rewritten_groups[group_name] = new_obj

    traverse_and_migrate(groups, rewritten_groups)
    
def traverse_and_migrate(groups, rewritten_groups, parent_id=None):
    for group in groups:
        if group.get("id") is None:
            break
        if rewritten_groups is not None:
            has_children = "child_ids" in rewritten_groups.get(group["id"], None)
        group_id = group["id"]
        group.pop("id")
        members = group["members"]
        group.pop("members")
        if group_id in rewritten_groups:
            try:
                api.generate_post_request(config.parent_host, config.parent_token, "groups", json.dumps(group))
            except urllib2.HTTPError, e:
                logging.info("Group already exists")
            new_group = json.load(api.generate_get_request(config.parent_host, config.parent_token, "groups?search=%s" % group["path"]))
            if new_group is not None and len(new_group) > 0:
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
                            api.generate_post_request(config.parent_host, config.parent_token, "groups/%d/members" % new_group[0]["id"], json.dumps(new_member))
                        except urllib2.HTTPError, e:
                            logging.error(e)

                    if not root_user_present:
                        logging.info("removing root user from group")
                        api.generate_delete_request(config.parent_host, config.parent_token, "groups/%d/members/1" % new_group[0]["id"])

                    if has_children:
                        subgroup = []
                        for sub in group["child_ids"]:
                            rewritten_groups.pop(group_id, None)
                            if rewritten_groups.get(sub) is not None:
                                sub_group = rewritten_groups.get(sub)
                                sub_group["parent_id"] = new_group[0]["id"]
                                subgroup.append(sub_group)
                        traverse_and_migrate(subgroup, rewritten_groups)
                    rewritten_groups.pop(group_id, None)

def append_groups(groups):
    with open("%s/data/groups.json" % app_path, "r") as f:
        group_file = json.load(f)
    staged_groups = []
    for group in groups:
        for g in group_file:
            if group == g["path"]:
                if g["parent_id"] is None:
                    if config.parent_id is not None:
                        g["parent_id"] = config.parent_id
                staged_groups.append(g)
    with open("%s/data/staged_groups.json" % app_path, "w") as f:
        json.dump(misc_utils.remove_dupes(staged_groups), f, indent=4)

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
