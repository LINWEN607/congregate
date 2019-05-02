"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import json
import argparse
import requests
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
        try:
            group.pop("ldap_cn")
            group.pop("ldap_access")
        except KeyError:
            pass
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
    count = 0
    for group in groups:
        l.logger.info("Migrating %s %d/%d" % (group["name"], count, len(group)))
        if group.get("id", None) is not None:
            if rewritten_groups is not None:
                has_children = "child_ids" in rewritten_groups.get(group["id"], None)
            group_id = group["id"]
            # group.pop("id")
            members = group["members"]
            
            # if group["visibility"] == "internal":
            #     group["visibility"] = "private"
            if group.get("parent_namespace", None) is not None:
                found = False
                if rewritten_groups.get(group["parent_id"], None) is not None:
                    parent_id = rewritten_groups[group["parent_id"]]["id"]
                elif group.get("old_parent_id", None) is not None:
                    if rewritten_groups.get(group["old_parent_id"], None) is not None:
                        parent_id = rewritten_groups[group["old_parent_id"]]["id"]
                
                #search = api.search(config.parent_host, config.parent_token, "groups", group["parent_namespace"])
                if parent_id is not None:
                    for s in api.list_all(config.parent_host, config.parent_token, "groups?search=%s" % group["parent_namespace"]):
                        if rewritten_groups.get(parent_id, None) is not None:
                            if s["full_path"].lower() == rewritten_groups[group["id"]]["full_parent_namespace"].lower():
                                group["parent_id"] = s["id"]
                                found = True
                                break
                    if found is False:
                        traverse_and_migrate([rewritten_groups[parent_id]], rewritten_groups)
                        search = api.search(config.parent_host, config.parent_token, "groups", group["parent_namespace"])
                        for s in search:
                            if rewritten_groups.get(parent_id, None) is not None:
                                if s["full_path"].lower() == rewritten_groups[parent_id]["full_path"].lower():
                                    group["parent_id"] = s["id"]
                                    found = True
                                    break
                else:
                    group["parent_id"] = None
                # group.pop("parent_namespace")
            else:
                print "Parent namespace is empty"

            # group.pop("full_path")
            
            new_group_id = None
            if group_id in rewritten_groups:
                try:
                    group_without_id = group.copy()
                    group_without_id.pop("id")
                    group_without_id.pop("full_path")
                    group_without_id.pop("members")
                    if group_without_id.get("parent_namespace", None) is not None:
                        group_without_id.pop("parent_namespace")
                        l.logger.debug("Popping parent group")
                    if group_without_id.get("full_parent_namespace", None) is not None:
                        group_without_id.pop("full_parent_namespace")
                        l.logger.debug("Popping parent namespace")
                    response = api.generate_post_request(config.parent_host, config.parent_token, "groups", json.dumps(group_without_id)).json()
                    if isinstance(response, dict):
                        if response.get("message", None) is not None:
                            if "Failed to save group" in response["message"]:
                                l.logger.info("Group already exists. Searching for group ID")
                                new_group = api.search(config.parent_host, config.parent_token, 'groups', group['path'])
                                if new_group is not None and len(new_group) > 0:
                                    for ng in new_group:
                                        if ng["name"] == group["name"]:
                                            new_group_id = ng["id"]
                                            l.logger.info("Group found")
                                            break
                            else:
                                l.logger.info("Failed to save group")
                        else:
                            new_group_id = response["id"]
                    elif isinstance(response, list):
                        new_group_id = response[0]["id"]
                except requests.exceptions.RequestException, e:
                    l.logger.info("Group already exists")
                if new_group_id is None:
                    new_group = api.search(config.parent_host, config.parent_token, 'groups', group['path'])
                    if new_group is not None and len(new_group) > 0:
                        for ng in new_group:
                            if ng["name"] == group["name"]:
                                if ng["parent_id"] == group["parent_id"] and group["parent_id"] == config.parent_id:
                                    new_group_id = ng["id"]
                                    l.logger.info("New group found")
                                    break
                if new_group_id:
                    root_user_present = False
                    for member in members:
                        if member["id"] == config.parent_user_id:
                            root_user_present = True
                        new_member = {
                            "user_id": member["id"],
                            "access_level": int(member["access_level"])
                        }

                        try:
                            response = api.generate_post_request(config.parent_host, config.parent_token, "groups/%d/members" % new_group_id, json.dumps(new_member))
                        except requests.exceptions.RequestException, e:
                            l.logger.error(e)

                    if not root_user_present:
                        l.logger.info("removing root user from group")
                        response = api.generate_delete_request(config.parent_host, config.parent_token, "groups/%d/members/%d" % (new_group_id, int(config.parent_user_id)))
                        print response

                    # if has_children:
                    #     subgroup = []
                    #     l.logger.info(group["child_ids"])
                    #     for sub in group["child_ids"]:
                    #         # rewritten_groups.pop(group_id, None)
                    #         l.logger.info(rewritten_groups.get(sub))
                    #         l.logger.info(rewritten_groups.keys())
                    #         if rewritten_groups.get(sub) is not None:
                    #             sub_group = rewritten_groups.get(sub)
                    #             sub_group["old_parent_id"] = sub_group["parent_id"]
                    #             sub_group["parent_id"] = new_group_id
                    #             subgroup.append(sub_group)
                    #     l.logger.info(subgroup)
                    #     traverse_and_migrate(subgroup, rewritten_groups)
                    # rewritten_groups.pop(group_id, None)
        else:
            print "Leaving recursion"

        count += 1 

def update_members():
    with open("%s/data/staged_groups.json" % app_path, "r") as f:
        groups = json.load(f)
    for group in groups:
        new_group_id = api.generate_get_request(config.parent_host, config.parent_token, 'groups', params={'search': group['name']}).json()
        print new_group_id
        members = group["members"]
        for member in members:
            if member["id"] == config.parent_user_id:
                root_user_present = True
            new_member = {
                "user_id": member["id"],
                "access_level": int(member["access_level"])
            }

            try:
                api.generate_post_request(config.parent_host, config.parent_token, "groups/%d/members" % new_group_id, json.dumps(new_member))
            except requests.exceptions.RequestException, e:
                l.logger.error(e)

def append_groups(groups):
    with open("%s/data/groups.json" % app_path, "r") as f:
        group_file = json.load(f)
    rewritten_groups = {}
    for i in range(len(group_file)):
        new_obj = group_file[i]
        group_name = group_file[i]["id"]
        rewritten_groups[group_name] = new_obj
    staged_groups = []
    if len(groups) > 0:
        if len(groups[0]) > 0:
            for group in groups:
                traverse_staging(int(group), rewritten_groups, staged_groups)
                l.logger.info("Staging group [%d/%d]" % (len(staged_groups), len(groups)))
                
    with open("%s/data/staged_groups.json" % app_path, "w") as f:
        json.dump(misc_utils.remove_dupes(staged_groups), f, indent=4)

def traverse_staging(id, group_dict, staged_groups):
    if group_dict.get(id, None) is not None:
        g = group_dict[id]
        if g["parent_id"] is None:
            if config.parent_id is not None:
                g["parent_id"] = config.parent_id
        else:
            parent_group = group_dict.get(g["parent_id"])
            if parent_group is not None:
                parent_group_name = api.generate_get_request(config.parent_host, config.parent_token, "groups/%d" % config.parent_id).json()["name"]
                g["full_parent_namespace"] = "%s/%s" % (parent_group_name, parent_group["full_path"])
                g["parent_namespace"] = parent_group["path"]
                if parent_group.get("parent_id", None) is not None:
                    traverse_staging(parent_group["id"], group_dict, staged_groups)
                else:
                    staged_groups.append(parent_group)
        staged_groups.append(g)
        

    
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

    parent_group = [api.generate_get_request(config.parent_host, config.parent_token, "groups/%d" % config.parent_id).json()]

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
            search_response = api.generate_get_request(config.parent_host, config.parent_token, 'groups', params={'search': group['name']}).json()
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
