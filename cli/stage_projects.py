"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import json
import sys
import subprocess
import re
try:
    from helpers import conf, api, misc_utils
    from helpers import logger as log
except ImportError:
    from congregate.helpers import conf, api, misc_utils
    from congregate.helpers import logger as log


app_path = os.getenv("CONGREGATE_PATH")
l = log.congregate_logger(__name__)

def stage_projects(projects_to_stage):
    staging = []
    staged_users = []
    staged_groups = []
    if (not os.path.isfile('%s/data/project_json.json' % app_path)):
        #TODO: rewrite this logic to handle subprocess more efficiently
        cmd = "%s/list_projects.sh > /dev/null" % app_path
        subprocess.call(cmd.split())

    config = conf.ig()

    # Loading projects information
    with open('%s/data/project_json.json' % app_path) as f:
        projects = json.load(f)

    with open("%s/data/groups.json" % app_path, "r") as f:
        groups = json.load(f)

    with open("%s/data/users.json" % app_path, "r") as f:
                users = json.load(f)

    # Rewriting projects to retrieve objects by ID more efficiently
    rewritten_projects = {}
    for i in range(len(projects)):
        new_obj = projects[i]
        id_num = projects[i]["id"]
        rewritten_projects[id_num] = new_obj

    rewritten_groups = {}
    for i in range(len(groups)):
        new_obj = groups[i]
        group_name = groups[i]["id"]
        rewritten_groups[group_name] = new_obj
    existing_parent_ids = []

    rewritten_users = {}
    for i in range(len(users)):
        new_obj = users[i]
        id_num = users[i]["username"]
        rewritten_users[id_num] = new_obj
    if not projects_to_stage[0] == '':
        if projects_to_stage[0] == "all" or projects_to_stage[0] == ".":
            for i in range(len(projects)):
                obj = {}
                obj["id"] = projects[i]["id"]
                obj["name"] = projects[i]["name"]
                obj["namespace"] = projects[i]["namespace"]["full_path"]
                obj["path_with_namespace"] = projects[i]["path_with_namespace"]
                obj["visibilty"] = projects[i]["visibility"]
                obj["http_url_to_repo"] = projects[i]["http_url_to_repo"]
                
                members = api.generate_get_request(config.child_host, config.child_token, "projects/%d/members" % int(projects[i]["id"])).json()
                
                for member in members:
                    if member["username"] != "root":
                        staged_users.append(rewritten_users[member["username"]])
                
                if projects[i]["namespace"]["kind"] == "group":
                    group_to_stage = projects[i]["namespace"]["path"]
                    staged_groups.append(rewritten_groups[group_to_stage])

                obj["members"] = members
                staging.append(obj)
        elif re.search(r"\d+-\d+", projects_to_stage[0]) is not None:
            match = (re.search(r"\d+-\d+", projects_to_stage[0])).group(0)
            start = int(match.split("-")[0])
            if start != 0:
                start -= 1
            end = int(match.split("-")[1]) - 1
            if end > len(projects):
                end = len(projects) - 1
            for i in range(start, end):
                obj = {}
                obj["id"] = projects[i]["id"]
                obj["name"] = projects[i]["name"]
                obj["namespace"] = projects[i]["namespace"]["full_path"]
                obj["path_with_namespace"] = projects[i]["path_with_namespace"]
                obj["visibilty"] = projects[i]["visibility"]
                obj["http_url_to_repo"] = projects[i]["http_url_to_repo"]
                
                members = api.generate_get_request(config.child_host, config.child_token, "projects/%d/members" % int(projects[i]["id"])).json()
                if isinstance(members, list):
                    for member in members:
                        if member["username"] != "root":
                            l.logger.info("Staging user (%s)" % member["username"])
                            staged_users.append(rewritten_users[member["username"]])
                
                if projects[0]["namespace"]["kind"] == "group":
                    group_to_stage = projects[0]["namespace"]["id"]
                    if rewritten_groups[group_to_stage]["parent_id"] is None:
                        if config.parent_id is not None:
                            rewritten_groups[group_to_stage]["parent_id"] = config.parent_id
                    else:
                        existing_parent_ids.append(rewritten_groups[group_to_stage]["id"])
                    staged_groups.append(rewritten_groups[group_to_stage])
                    if "child_ids" in rewritten_groups[group_to_stage]:
                        for sub in rewritten_groups[group_to_stage]["child_ids"]:
                            staged_groups.append(rewritten_groups[sub])
                    if len(rewritten_groups[group_to_stage]["members"]) > 0:
                        for member in rewritten_groups[group_to_stage]["members"]:
                            if rewritten_users.get(member["username"]):
                                staged_users.append(rewritten_users[member["username"]])

                obj["members"] = members
                l.logger.info("Staging project (%s) [%d/%d]" % (obj["name"], len(staging)+1, len(range(start, end))))
                staging.append(obj)
        else:
            for i in range(0, len(projects_to_stage)):
                obj = {}
                # Hacky check for id or project name by explicitly checking variable type
                try:
                    if (isinstance(int(projects_to_stage[i]), int)):
                        key = projects_to_stage[i]
                        # Retrieve object from better formatted object
                        project = rewritten_projects[int(key)]
                except ValueError:
                    # Iterate over original project_json.json file
                    for j in range(len(projects)):
                        if projects[j]["name"] == projects_to_stage[i]:
                            project = projects[j]

                obj["id"] = project["id"]
                obj["name"] = project["name"]
                obj["namespace"] = project["namespace"]["full_path"]
                obj["visibilty"] = project["visibility"]
                obj["http_url_to_repo"] = project["http_url_to_repo"]
                obj["project_type"] = project["namespace"]["kind"]

                members = api.generate_get_request(config.child_host, config.child_token, "projects/%d/members" % int(project["id"])).json()
                if isinstance(members, list):
                    for member in members:
                        if member["username"] != "root":
                            l.logger.info("Staging user (%s)" % member["username"])
                            staged_users.append(rewritten_users[member["username"]])
                
                if project["namespace"]["kind"] == "group":
                    group_to_stage = project["namespace"]["id"]
                    if rewritten_groups[group_to_stage]["parent_id"] is None:
                        if config.parent_id is not None:
                            rewritten_groups[group_to_stage]["parent_id"] = config.parent_id
                    else:
                        existing_parent_ids.append(rewritten_groups[group_to_stage]["id"])
                    staged_groups.append(rewritten_groups[group_to_stage])
                    if "child_ids" in rewritten_groups[group_to_stage]:
                        for sub in rewritten_groups[group_to_stage]["child_ids"]:
                            staged_groups.append(rewritten_groups[sub])
                    if len(rewritten_groups[group_to_stage]["members"]) > 0:
                        for member in rewritten_groups[group_to_stage]["members"]:
                            if rewritten_users.get(member["username"]):
                                staged_users.append(rewritten_users[member["username"]])

                obj["members"] = members
                l.logger.info("Staging project (%s) [%d/%d]" % (obj["name"], len(staging), len(projects_to_stage)))
                staging.append(obj)
    else:
        staging = []

    for group in staged_groups:
        if group["parent_id"] not in existing_parent_ids:
            group["parent_id"] = config.parent_id
    if (len(staging) > 0):
        with open("%s/data/stage.json" % app_path, "wb") as f:
            f.write(json.dumps(misc_utils.remove_dupes(staging), indent=4))
        with open("%s/data/staged_users.json" % app_path, "wb") as f:
            f.write(json.dumps(misc_utils.remove_dupes(staged_users), indent=4))
        with open("%s/data/staged_groups.json" % app_path, "wb") as f:
            f.write(json.dumps(misc_utils.remove_dupes(staged_groups), indent=4))
    else:
        with open("%s/data/stage.json" % app_path, "wb") as f:
            f.write("[]")

if __name__ == "__main__":
    stage_projects(sys.argv)

