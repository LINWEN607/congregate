"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import json
import sys
import subprocess
import re
from helpers import misc_utils
from helpers import base_module as b
from migration.gitlab.projects import ProjectsClient

proj_client = ProjectsClient()

def stage_projects(projects_to_stage):
    staging = []
    staged_users = []
    staged_groups = []
    if (not os.path.isfile('%s/data/project_json.json' % b.app_path)):
        #TODO: rewrite this logic to handle subprocess more efficiently
        cmd = "%s/list_projects.sh > /dev/null" % b.app_path
        subprocess.call(cmd.split())

    # Loading projects information
    with open('%s/data/project_json.json' % b.app_path) as f:
        projects = json.load(f)

    with open("%s/data/groups.json" % b.app_path, "r") as f:
        groups = json.load(f)

    with open("%s/data/users.json" % b.app_path, "r") as f:
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
                
                members = []
                for member in proj_client.get_members(int(projects[i]["id"]), b.config.child_host, b.config.child_token):
                    if member["username"] != "root":
                        staged_users.append(rewritten_users[member["username"]])
                        members.append(member)
                
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
                
                members = []
                for member in proj_client.get_members(int(projects[i]["id"]), b.config.child_host, b.config.child_token):
                    if member["username"] != "root":
                        b.l.logger.info("Staging user (%s)" % member["username"])
                        staged_users.append(rewritten_users[member["username"]])
                        members.append(member)
                
                if projects[0]["namespace"]["kind"] == "group":
                    group_to_stage = projects[0]["namespace"]["id"]
                    if rewritten_groups[group_to_stage]["parent_id"] is None:
                        if b.config.parent_id is not None:
                            rewritten_groups[group_to_stage]["parent_id"] = b.config.parent_id
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
                b.l.logger.info("Staging project (%s) [%d/%d]" % (obj["name"], len(staging)+1, len(range(start, end))))
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

                members = []
                for member in proj_client.get_members(int(project["id"]), b.config.child_host, b.config.child_token):
                    if member["username"] != "root":
                        b.l.logger.info("Staging user (%s)" % member["username"])
                        staged_users.append(rewritten_users[member["username"]])
                        members.append(member)
                
                if project["namespace"]["kind"] == "group":
                    group_to_stage = project["namespace"]["id"]
                    if rewritten_groups[group_to_stage]["parent_id"] is None:
                        if b.config.parent_id is not None:
                            rewritten_groups[group_to_stage]["parent_id"] = b.config.parent_id
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
                b.l.logger.info("Staging project (%s) [%d/%d]" % (obj["name"], len(staging), len(projects_to_stage)))
                staging.append(obj)
    else:
        staging = []

    for group in staged_groups:
        if group["parent_id"] not in existing_parent_ids:
            group["parent_id"] = b.config.parent_id
    if (len(staging) > 0):
        with open("%s/data/stage.json" % b.app_path, "wb") as f:
            f.write(json.dumps(misc_utils.remove_dupes(staging), indent=4))
        with open("%s/data/staged_users.json" % b.app_path, "wb") as f:
            f.write(json.dumps(misc_utils.remove_dupes(staged_users), indent=4))
        with open("%s/data/staged_groups.json" % b.app_path, "wb") as f:
            f.write(json.dumps(misc_utils.remove_dupes(staged_groups), indent=4))
    else:
        with open("%s/data/stage.json" % b.app_path, "wb") as f:
            f.write("[]")
