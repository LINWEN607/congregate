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
    from helpers import logger as log
except ImportError:
    from congregate.helpers import conf, api, misc_utils
    from congregate.helpers import logger as log

app_path = os.getenv("CONGREGATE_PATH")
l = log.congregate_logger(__name__)
config = conf.ig()

def traverse_groups(base_groups, transient_list,  host, token, parent_group=None):
    if parent_group is not None:
        parent_group["child_ids"] = []
    for group in base_groups:
        group.pop("web_url")
        group.pop("full_name")
        group.pop("full_path")
        group.pop("ldap_cn")
        group.pop("ldap_access")
        members = list(api.list_all(host, token, "groups/%s/members" % str(group["id"])))
        group["members"] = members
        transient_list.append(group)
        subgroups = list(api.list_all(host, token, "groups/%s/subgroups" % str(group["id"])))
        if parent_group is not None:
            parent_group["child_ids"].append(group["id"])
        if len(subgroups) > 0:
            parent_group = transient_list[-1]
            l.logger.info("traversing into a subgroup")
            traverse_groups(subgroups, transient_list, host, token, parent_group)
        else:
            l.logger.info("No subgroups found")
        parent_group = None
            

def retrieve_group_info(quiet=False):
    groups = list(api.list_all(config.child_host, config.child_token, "groups"))
    transient_list = []

    traverse_groups(groups, transient_list, config.child_host, config.child_token)

    with open('%s/data/groups.json' % app_path, "w") as f:
        json.dump(groups, f, indent=4)
    
    if not quiet:
        l.logger.info("Retrieved %d groups. Check groups.json to see all retrieved groups" % len(groups))

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
        #print group
        if group.get("id") is not None:
            if rewritten_groups is not None:
                has_children = "child_ids" in rewritten_groups.get(group["id"], None)
            group_id = group["id"]
            group.pop("id")
            members = group["members"]
            group.pop("members")
            if group["visibility"] == "internal":
                group["visibility"] = "private"
            new_group_id = None
            if group_id in rewritten_groups:
                try:
                    response = json.load(api.generate_post_request(config.parent_host, config.parent_token, "groups", json.dumps(group)))
                    new_group_id = response["id"]
                except urllib2.HTTPError, e:
                    l.logger.info(json.dumps(e.read()))
                    l.logger.info("Group already exists")
                # if not new_group_id:
                #     new_group = json.load(api.generate_get_request(config.parent_host, config.parent_token, "groups?search=%s" % group["path"]))
                #     if new_group is not None and len(new_group) > 0:
                #         for ng in new_group:
                #             if ng["name"] == group["name"]:
                #                 if ng["parent_id"] == group["parent_id"] and group["parent_id"] == config.parent_id:
                #                     new_group_id = ng["id"]
                #                     l.logger.info("New group found")
                #                     break
                if new_group_id:
                    root_user_present = False
                    for member in members:
                        if member["id"] == config.parent_user_id:
                            root_user_present = True
                        new_member = {
                            "user_id": member["id"],
                            "access_level": member["access_level"]
                        }

                        try:
                            api.generate_post_request(config.parent_host, config.parent_token, "groups/%d/members" % new_group_id, json.dumps(new_member))
                        except urllib2.HTTPError, e:
                            l.logger.error(e)

                    if not root_user_present:
                        l.logger.info("removing root user from group")
                        api.generate_delete_request(config.parent_host, config.parent_token, "groups/%d/members/%d" % (new_group_id, int(config.parent_user_id)))

                    if has_children:
                        subgroup = []
                        for sub in group["child_ids"]:
                            rewritten_groups.pop(group_id, None)
                            if rewritten_groups.get(sub) is not None:
                                sub_group = rewritten_groups.get(sub)
                                sub_group["parent_id"] = new_group_id
                                subgroup.append(sub_group)
                        l.logger.info(subgroup)
                        traverse_and_migrate(subgroup, rewritten_groups)
                    rewritten_groups.pop(group_id, None)
        else:
            print "Leaving recursion"

def update_members():
    with open("%s/data/staged_groups.json" % app_path, "r") as f:
        groups = json.load(f)
    for group in groups:
        new_group_id = json.load(api.generate_get_request(config.parent_host, config.parent_token, "groups?search=%s" % group["name"]))[0]["id"]
        print new_group_id
        members = group["members"]
        for member in members:
            if member["id"] == config.parent_user_id:
                root_user_present = True
            new_member = {
                "user_id": member["id"],
                "access_level": member["access_level"]
            }

            try:
                api.generate_post_request(config.parent_host, config.parent_token, "groups/%d/members" % new_group_id, json.dumps(new_member))
            except urllib2.HTTPError, e:
                l.logger.error(e)

def append_groups(groups):
    with open("%s/data/groups.json" % app_path, "r") as f:
        group_file = json.load(f)
    staged_groups = []
    if len(groups) > 0:
        if len(groups[0]) > 0:
            for group in groups:
                for g in group_file:
                    if int(group) == g["id"]:
                        if g["parent_id"] is None:
                            if config.parent_id is not None:
                                g["parent_id"] = config.parent_id
                        else:
                            if g["parent_id"] not in groups:
                                g["parent_id"] = config.parent_id
                        staged_groups.append(g)
    with open("%s/data/staged_groups.json" % app_path, "w") as f:
        json.dump(misc_utils.remove_dupes(staged_groups), f, indent=4)
    
def find_all_internal_projects():
    groups_to_change = []
    # with open("%s/data/groups.json" % app_path, "r") as f:
    #     groups = json.load(f)
    # count = 0
    # for group in groups:
    #     if group["visibility"] != "private":
    #         l.logger.info("%s has %s visibility" % (group["name"], group["visibility"]))
    #         count += 1
    #         groups_to_change.append(group)

    # l.logger.info("There are %d non-private groups" % count)

    transient_list = []

    parent_group = [json.load(api.generate_get_request(config.parent_host, config.parent_token, "groups/%d" % config.parent_id))]

    print parent_group

    traverse_groups(parent_group, transient_list, config.parent_host, config.parent_token)

    count = 0

    for group in transient_list:
        print "%s, %s" % (group["name"], group["visibility"])
        if group["visibility"] != "private":
            l.logger.info("%s has %s visibility" % (group["name"], group["visibility"]))
            count += 1
            groups_to_change.append(group)

    return groups_to_change

def make_all_internal_groups_private():
    groups = find_all_internal_projects()
    ids = []
    for group in groups:
        try:
            l.logger.debug("Searching for existing %s" % group["name"])
            search_response = json.load(api.generate_get_request(config.parent_host, config.parent_token, "groups?search=%s" % (group["name"])))
            if len(search_response) > 0:
                for proj in search_response:
                    if proj["name"] == group["name"]:
                        if "%s" % group["path"].lower() in proj["full_path"].lower():
                            #l.logger.info("Migrating variables for %s" % proj["name"])
                            ids.append(proj["id"])
                            print "%s: %s" % (proj["full_path"], proj["visibility"])
                            break
        except IOError, e:
            l.logger.error(e)
    print ids


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
