"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

import json
import re

from congregate.helpers.misc_utils import get_dry_log, remove_dupes
from congregate.helpers.base_class import BaseClass

b = BaseClass()

staged_users, staged_groups, staged_projects = [], [], []
rewritten_users, rewritten_groups, rewritten_projects = {}, {}, {}


def stage_data(projects_to_stage, dry_run=True, skip_users=False):
    """
        Stage data based on selected projects on source instance

        :param: projects_to_stage: (dict) the staged projects object
        :param: dry_run (bool) If true, it will only build the staging data lists
        :param: skip_users (bool) If true will skip writing staged users to file
    """
    build_staging_data(projects_to_stage, dry_run)
    if not dry_run:
        write_staging_files(skip_users=skip_users)


def build_staging_data(projects_to_stage, dry_run=True):
    """
        Build data up from project level, including groups and users (members)

        :param: projects_to_stage: (dict) the staged projects objects
        :param: dry_run (bool) dry_run (bool) If true, it will only build the staging data lists.
    """
    # Loading projects information
    projects = open_projects_file()
    groups = open_groups_file()
    users = open_users_file()

    # Rewriting projects to retrieve objects by ID more efficiently
    for i, _ in enumerate(projects):
        rewritten_projects[projects[i]["id"]] = projects[i]

    for i, _ in enumerate(groups):
        rewritten_groups[groups[i]["id"]] = groups[i]

    for i, _ in enumerate(users):
        rewritten_users[users[i]["id"]] = users[i]

    # If there is CLI or UI input
    if filter(None, projects_to_stage):
        # Stage ALL
        if projects_to_stage[0] in ["all", "."] or len(projects_to_stage) == len(projects):
            for p in projects:
                b.log.info("{0}Staging project {1} (ID: {2})".format(
                    get_dry_log(dry_run), p["path_with_namespace"], p["id"]))
                staged_projects.append(get_project_metadata(p))

            for g in groups:
                b.log.info("{0}Staging group {1} (ID: {2})".format(
                    get_dry_log(dry_run), g["full_path"], g["id"]))
                # Decrease size of staged_groups.json
                g.pop("projects", None)
                staged_groups.append(g)

            for u in users:
                b.log.info("{0}Staging user {1} (ID: {2})".format(
                    get_dry_log(dry_run), u["username"], u["id"]))
                staged_users.append(u)
        # CLI range input
        elif re.search(r"\d+-\d+", projects_to_stage[0]) is not None:
            match = (re.search(r"\d+-\d+", projects_to_stage[0])).group(0)
            start = int(match.split("-")[0])
            if start != 0:
                start -= 1
            end = int(match.split("-")[1])
            for i in range(start, end):
                append_data(projects[i], projects_to_stage, p_range=range(
                    start, end), dry_run=dry_run)
        # Random selection
        else:
            for i, _ in enumerate(projects_to_stage):
                # Hacky check for id or project name by explicitly checking
                # variable type
                try:
                    # Retrieve group object from groups.json
                    project = rewritten_projects[int(
                        re.sub("[^0-9]", "", projects_to_stage[i]))]
                except (ValueError, KeyError):
                    b.log.error("Please use a space delimited list of integers (project IDs):\n{}".format(
                        projects_to_stage))
                    exit()
                append_data(project, projects_to_stage, dry_run=dry_run)
    else:
        b.log.info("Staging empty list")
        return staged_users, staged_groups, staged_projects
    return remove_dupes(staged_projects), remove_dupes(
        staged_users), remove_dupes(staged_groups)


def append_data(project, projects_to_stage, p_range=0, dry_run=True):
    obj = get_project_metadata(project)
    for member in obj["members"]:
        append_member_to_members_list([], member, dry_run)

    if obj["project_type"] == "group":
        group_to_stage = rewritten_groups[project["namespace"]["id"]]
        b.log.info("{0}Staging group {1} (ID: {2})".format(get_dry_log(
            dry_run), group_to_stage["full_path"], group_to_stage["id"]))
        group_to_stage.pop("projects", None)
        staged_groups.append(group_to_stage)

        # Append all group members to staged users
        for member in group_to_stage["members"]:
            append_member_to_members_list([], member, dry_run)

    b.log.info("{0}Staging project {1} (ID: {2}) [{3}/{4}]".format(get_dry_log(
        dry_run), obj["path_with_namespace"], obj["id"], len(staged_projects) + 1, len(p_range) if p_range else len(projects_to_stage)))
    staged_projects.append(obj)


def open_projects_file():
    """
        Open project.json file to read, turning JSON encoded data to projects.

        :return: projects object
    """
    with open('%s/data/project_json.json' % b.app_path, "r") as f:
        return json.load(f)


def open_groups_file():
    """
        Open group.json file to read, turning JSON encoded data to groups object.

        :return: groups object
    """
    with open("%s/data/groups.json" % b.app_path, "r") as f:
        return json.load(f)


def open_users_file():
    """
        Open users.json file to read, turning JSON encoded data to users object.

        :return: users object
    """
    with open("%s/data/users.json" % b.app_path, "r") as f:
        return json.load(f)


def write_staging_files(skip_users=False):
    """
        Write all staged projects, users and groups objects into JSON files

        :param: staging: (dict) staged projects
        :param: staged_users:(dict) staged users
        :param: staged_groups: (dict) staged groups
    """
    with open("%s/data/staged_projects.json" % b.app_path, "wb") as f:
        f.write(json.dumps(remove_dupes(staged_projects), indent=4))
    with open("%s/data/staged_groups.json" % b.app_path, "wb") as f:
        f.write(json.dumps(remove_dupes(staged_groups), indent=4))
    with open("%s/data/staged_users.json" % b.app_path, "wb") as f:
        f.write(json.dumps([] if skip_users else remove_dupes(staged_users), indent=4))


def append_member_to_members_list(members_list, member, dry_run=True):
    """
        Appends the members found in the /members endpoint to the staged asset object

        params: rewritten_users: object containing the various users from the instance
        params: staged_users:  object containing the specific users to be staged
        params: member_users: object containing the specific members of the group or project
        params: rewritten_users: object containing the specific member to be added to the group or project
    """
    if isinstance(member, dict):
        if member.get("id", None) is not None:
            b.log.info("{0}Staging user {1} (ID: {2})".format(
                get_dry_log(dry_run), member["username"], member["id"]))
            staged_users.append(
                rewritten_users[member["id"]])
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
        "path": project["path"],
        "path_with_namespace": project["path_with_namespace"],
        "visibility": project["visibility"],
        "description": project["description"],
        "project_type": project["namespace"]["kind"],
        "members": project["members"]
    }
    if b.config.source_type == "GitLab":
        obj["http_url_to_repo"] = project["http_url_to_repo"]
        obj["shared_runners_enabled"] = project["shared_runners_enabled"]
        obj["archived"] = project["archived"]
        obj["shared_with_groups"] = project["shared_with_groups"]

        # In case of projects without repos (e.g. Wiki)
        if "default_branch" in project:
            obj["default_branch"] = project["default_branch"]
    return obj
