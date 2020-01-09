"""
Congregate - GitLab instance migration utility 

Copyright (c) 2020 - GitLab
"""

import json
import re
from congregate.helpers.misc_utils import get_dry_log, remove_dupes, is_non_empty_file
from congregate.helpers import base_module as b
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.cli.list_projects import list_projects

projects_api = ProjectsApi()
existing_parent_ids = []

# TODO: Break down into separate staging areas
def stage_projects(projects_to_stage, dry_run=True):
    staged_projects, staged_users, staged_groups = build_staging_data(
        projects_to_stage, dry_run)
    if not dry_run:
        write_staging_files(staged_projects, staged_users, staged_groups)


def build_staging_data(projects_to_stage, dry_run=True):
    staging = []
    staged_users = []
    staged_groups = []

    # List projects
    if not is_non_empty_file("{}/data/project_json.json".format(b.app_path)):
        list_projects()

    # Loading projects information
    projects = open_projects_file()
    groups = open_groups_file()
    users = open_users_file()

    # Rewriting projects to retrieve objects by ID more efficiently
    rewritten_projects = {}
    for i in range(len(projects)):
        new_obj = projects[i]
        id_num = projects[i]["id"]
        rewritten_projects[id_num] = new_obj

    rewritten_groups = {}
    for i in range(len(groups)):
        new_obj = groups[i]
        group_id = groups[i]["id"]
        rewritten_groups[group_id] = new_obj

    rewritten_users = {}
    for i in range(len(users)):
        new_obj = users[i]
        id_num = users[i]["username"]
        rewritten_users[id_num] = new_obj

    if not projects_to_stage[0] == "":
        if projects_to_stage[0] == "all" or projects_to_stage[0] == ".":
            for i in range(len(projects)):
                obj = get_project_metadata(projects[i])

                members = []
                for member in projects_api.get_members(int(projects[i]["id"]), b.config.source_host, b.config.source_token):
                    append_member_to_members_list(rewritten_users, staged_users, members, member)

                if projects[i]["namespace"]["kind"] == "group":
                    group_to_stage = projects[i]["namespace"]["id"]
                    staged_groups.append(rewritten_groups[group_to_stage])

                obj["members"] = members
                staging.append(obj)
        elif re.search(r"\d+-\d+", projects_to_stage[0]) is not None:
            match = (re.search(r"\d+-\d+", projects_to_stage[0])).group(0)
            start = int(match.split("-")[0])
            if start != 0:
                start -= 1
            end = int(match.split("-")[1])
            for i in range(start, end):
                obj = get_project_metadata(projects[i])

                members = []
                for member in projects_api.get_members(int(projects[i]["id"]), b.config.source_host, b.config.source_token):
                    append_member_to_members_list(rewritten_users, staged_users, members, member)

                if projects[0]["namespace"]["kind"] == "group":
                    group_to_stage = projects[0]["namespace"]["id"]
                    if rewritten_groups[group_to_stage]["parent_id"] is None:
                        if b.config.parent_id is not None:
                            rewritten_groups[group_to_stage]["parent_id"] = b.config.parent_id
                    else:
                        existing_parent_ids.append(
                            rewritten_groups[group_to_stage]["id"])
                    staged_groups.append(rewritten_groups[group_to_stage])
                    if "child_ids" in rewritten_groups[group_to_stage]:
                        for sub in rewritten_groups[group_to_stage]["child_ids"]:
                            staged_groups.append(rewritten_groups[sub])
                    if len(rewritten_groups[group_to_stage]["members"]) > 0:
                        for member in rewritten_groups[group_to_stage]["members"]:
                            if rewritten_users.get(member["username"]):
                                staged_users.append(
                                    rewritten_users[member["username"]])

                obj["members"] = members
                b.log.info("{0}Staging project ({1}) [{2}/{3}]".format(
                    get_dry_log(dry_run),
                    obj["name"],
                    len(staging)+1,
                    len(range(start, end))))
                staging.append(obj)
        else:
            for i in range(0, len(projects_to_stage)):
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

                obj = get_project_metadata(project)

                members = []
                for member in projects_api.get_members(int(project["id"]), b.config.source_host, b.config.source_token):
                    append_member_to_members_list(rewritten_users, staged_users, members, member)
                    
                if project["namespace"]["kind"] == "group":
                    group_to_stage = project["namespace"]["id"]
                    if rewritten_groups[group_to_stage]["parent_id"] is None:
                        if b.config.parent_id is not None:
                            rewritten_groups[group_to_stage]["parent_id"] = b.config.parent_id
                    else:
                        existing_parent_ids.append(
                            rewritten_groups[group_to_stage]["id"])
                    staged_groups.append(rewritten_groups[group_to_stage])
                    if "child_ids" in rewritten_groups[group_to_stage]:
                        for sub in rewritten_groups[group_to_stage]["child_ids"]:
                            staged_groups.append(rewritten_groups[sub])
                    if len(rewritten_groups[group_to_stage]["members"]) > 0:
                        for member in rewritten_groups[group_to_stage]["members"]:
                            if rewritten_users.get(member["username"]):
                                staged_users.append(
                                    rewritten_users[member["username"]])

                obj["members"] = members
                b.log.info("{0}Staging project ({1}) [{2}/{3}]".format(
                    get_dry_log(dry_run),
                    obj["name"],
                    len(staging),
                    len(projects_to_stage)))
                staging.append(obj)
    else:
        staging = []

    return remove_dupes(staging), remove_dupes(staged_users), remove_dupes(staged_groups)


def open_projects_file():
    with open('%s/data/project_json.json' % b.app_path, "r") as f:
        projects = json.load(f)
    return projects


def open_groups_file():
    with open("%s/data/groups.json" % b.app_path, "r") as f:
        groups = json.load(f)
    return groups


def open_users_file():
    with open("%s/data/users.json" % b.app_path, "r") as f:
        users = json.load(f)
    return users


def write_staging_files(staging, staged_users, staged_groups):
    for group in staged_groups:
        if group["parent_id"] not in existing_parent_ids:
            group["parent_id"] = b.config.parent_id
    if (len(staging) > 0):
        with open("%s/data/stage.json" % b.app_path, "wb") as f:
            f.write(json.dumps(staging, indent=4))
        with open("%s/data/staged_users.json" % b.app_path, "wb") as f:
            f.write(json.dumps(staged_users, indent=4))
        with open("%s/data/staged_groups.json" % b.app_path, "wb") as f:
            f.write(json.dumps(staged_groups, indent=4))
    else:
        with open("%s/data/stage.json" % b.app_path, "wb") as f:
            f.write("[]")

def append_member_to_members_list(rewritten_users, staged_users, members_list, member):
    if isinstance(member, dict):
        if member.get("username", None) is not None:
            if member["username"] != "root":
                b.log.info("Staging user (%s)" % member["username"])
                staged_users.append(
                    rewritten_users[member["username"]])
                members_list.append(member)
    else:
        b.log.error(member)

def get_project_metadata(project):
    obj = {
        "id": project["id"],
        "name": project["name"],
        "namespace": project["namespace"]["full_path"],
        "visibility": project["visibility"],
        "http_url_to_repo": project["http_url_to_repo"],
        "project_type": project["namespace"]["kind"],
        "description": project["description"],
        "shared_runners_enabled": project["shared_runners_enabled"],
        "archived": project["archived"]
    }

    # In case of projects without repos (e.g. Wiki)
    if "default_branch" in project:
        obj["default_branch"] = project["default_branch"]
    # *_access_level in favor of the deprecated *_enabled keys. Only for version >= 12
    obj["wiki_access_level"] = "enabled" if project["wiki_enabled"] else "disabled"
    obj["issues_access_level"] = "enabled" if project["issues_enabled"] else "disabled"
    obj["merge_requests_access_level"] = "enabled" if project["merge_requests_enabled"] else "disabled"
    obj["builds_access_level"] = "enabled" if project["jobs_enabled"] else "disabled"
    obj["snippets_access_level"] = "enabled" if project["snippets_enabled"] else "disabled"
    obj["repository_access_level"] = "enabled" if project["issues_enabled"] and project["merge_requests_enabled"] else "disabled"

    return obj
