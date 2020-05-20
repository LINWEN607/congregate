"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

import json
import re
from congregate.helpers.misc_utils import get_dry_log, remove_dupes
from congregate.helpers.migrate_utils import is_top_level_group
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.projects import ProjectsApi

projects_api = ProjectsApi()
existing_parent_ids = []
b = BaseClass()

# TODO: Break down into separate staging areas
# Stage users, groups and projects


def stage_projects(projects_to_stage, dry_run=True):
    """
        Stage all the projects from the source instance

        :param: projects_to_stage: (dict) the staged projects objects
        :param: dry_run (bool) If true, it will only build the staging data lists
    """
    staged_projects, staged_users, staged_groups = build_staging_data(
        projects_to_stage, dry_run)
    if not dry_run:
        write_staging_files(staged_projects, staged_users, staged_groups)


def build_staging_data(projects_to_stage, dry_run=True):
    """
        Stage all the data including project, groups and users from the source instance

        :param: projects_to_stage: (dict) the staged projects objects
        :param: dry_run (bool) dry_run (bool) If true, it will only build the staging data lists.
    """
    staging = []
    staged_users = []
    staged_groups = []

    # Loading projects information
    projects = open_projects_file()
    groups = open_groups_file()
    users = open_users_file()

    # Rewriting projects to retrieve objects by ID more efficiently
    rewritten_projects = {}
    for i, _ in enumerate(projects):
        new_obj = projects[i]
        id_num = projects[i]["id"]
        rewritten_projects[id_num] = new_obj

    rewritten_groups = {}
    for i, _ in enumerate(groups):
        new_obj = groups[i]
        group_id = groups[i]["id"]
        rewritten_groups[group_id] = new_obj

    rewritten_users = {}
    for i, _ in enumerate(users):
        new_obj = users[i]
        id_num = users[i]["username"]
        rewritten_users[id_num] = new_obj

    if not projects_to_stage[0] == "":
        if projects_to_stage[0] == "all" or projects_to_stage[0] == ".":
            # Stage ALL projects
            for i, _ in enumerate(projects):
                obj = get_project_metadata(projects[i])

                members = []
                for member in projects_api.get_members(
                        int(projects[i]["id"]), b.config.source_host, b.config.source_token):
                    append_member_to_members_list(
                        rewritten_users, staged_users, members, member)

                obj["members"] = members
                staging.append(obj)

            # Stage ALL groups
            for g in groups:
                b.log.info("Staging {0} {1} (ID: {2})".format(
                    "top-level group" if is_top_level_group(g) else "sub-group", g["full_path"], g["id"]))
                staged_groups.append(g)

            # Stage ALL users
            for user in users:
                staged_users.append(user)
        elif re.search(r"\d+-\d+", projects_to_stage[0]) is not None:
            match = (re.search(r"\d+-\d+", projects_to_stage[0])).group(0)
            start = int(match.split("-")[0])
            if start != 0:
                start -= 1
            end = int(match.split("-")[1])
            for i in range(start, end):
                obj = get_project_metadata(projects[i])

                members = []
                for member in projects_api.get_members(
                        int(projects[i]["id"]), b.config.source_host, b.config.source_token):
                    append_member_to_members_list(
                        rewritten_users, staged_users, members, member)

                if projects[0]["namespace"]["kind"] == "group":
                    group_to_stage = projects[0]["namespace"]["id"]
                    if rewritten_groups[group_to_stage]["parent_id"] is None:
                        if b.config.dstn_parent_id is not None:
                            rewritten_groups[group_to_stage]["parent_id"] = b.config.dstn_parent_id
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
                    len(staging) + 1,
                    len(range(start, end))))
                staging.append(obj)
        else:
            for i, _ in enumerate(projects_to_stage):
                # Hacky check for id or project name by explicitly checking
                # variable type
                try:
                    if (isinstance(int(projects_to_stage[i]), int)):
                        key = projects_to_stage[i]
                        # Retrieve object from better formatted object
                        project = rewritten_projects[int(key)]
                except ValueError:
                    # Iterate over original project_json.json file
                    for j, _ in enumerate(projects):
                        if projects[j]["name"] == projects_to_stage[i]:
                            project = projects[j]

                obj = get_project_metadata(project)

                members = []
                for member in projects_api.get_members(
                        int(project["id"]), b.config.source_host, b.config.source_token):
                    append_member_to_members_list(
                        rewritten_users, staged_users, members, member)

                if project["namespace"]["kind"] == "group":
                    group_to_stage = project["namespace"]["id"]
                    if rewritten_groups[group_to_stage]["parent_id"] is None:
                        if b.config.dstn_parent_id is not None:
                            rewritten_groups[group_to_stage]["parent_id"] = b.config.dstn_parent_id
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

    return remove_dupes(staging), remove_dupes(
        staged_users), remove_dupes(staged_groups)


def open_projects_file():
    """
        Open project.json file to read, turning JSON encoded data to projects.

        :return: projects object
    """
    with open('%s/data/project_json.json' % b.app_path, "r") as f:
        projects = json.load(f)
    return projects


def open_groups_file():
    """
        Open group.json file to read, turning JSON encoded data to groups object.

        :return: groups object
    """
    with open("%s/data/groups.json" % b.app_path, "r") as f:
        groups = json.load(f)
    return groups


def open_users_file():
    """
        Open users.json file to read, turning JSON encoded data to users object.

        :return: users object
    """
    with open("%s/data/users.json" % b.app_path, "r") as f:
        users = json.load(f)
    return users


def write_staging_files(staging, staged_users, staged_groups):
    """
        Write all staged projects, users and groups objects into JSON files

        :param: staging: (dict) staged projects
        :param: staged_users:(dict) staged users
        :param: staged_groups: (dict) staged groups
    """
    for group in staged_groups:
        if group["parent_id"] not in existing_parent_ids:
            group["parent_id"] = b.config.dstn_parent_id
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


def append_member_to_members_list(
        rewritten_users, staged_users, members_list, member):
    """
        Appends the members found in the /members endpoint to the staged asset object

        params: rewritten_users: object containing the various users from the instance
        params: staged_users:  object containing the specific users to be staged
        params: member_users: object containing the specific members of the group or project
        params: rewritten_users: object containing the specific member to be added to the group or project
    """
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
    """
        Get the object data providing project information

        :param project: (str) project information
        :return: obj object
    """
    obj = {
        "id": project["id"],
        "name": project["name"],
        "namespace": project["namespace"]["full_path"],
        "visibility": project["visibility"],
        "http_url_to_repo": project["http_url_to_repo"],
        "project_type": project["namespace"]["kind"],
        "description": project["description"],
        "shared_runners_enabled": project["shared_runners_enabled"],
        "archived": project["archived"],
        "path_with_namespace": project["path_with_namespace"],
        "path": project["path"],
        "shared_with_groups": project["shared_with_groups"]
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
