"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

import json
import re

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import get_dry_log, remove_dupes
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi

projects_api = ProjectsApi()
groups_api = GroupsApi()
b = BaseClass()

staged_users, staged_groups, staged_projects = [], [], []
rewritten_users, rewritten_groups, rewritten_projects = {}, {}, {}


def stage_groups(groups_to_stage, dry_run=True, skip_users=False):
    """
        Stage all groups from the source instance

        :param: groups_to_stage: (dict) the staged groups object
        :param: dry_run (bool) If true, it will only build the staging data lists
        :param: skip_users (bool) If true will skip writing staged users to file
    """
    build_staging_data(groups_to_stage, dry_run)
    if not dry_run:
        write_staging_files(skip_users=skip_users)


def build_staging_data(groups_to_stage, dry_run=True, skip_users=False):
    """
        Stage all the data including project, groups and users from the source instance

        :param: groups_to_stage: (dict) the staged groups objects
        :param: dry_run (bool) If true, it will only build the staging data lists.
    """
    # Loading projects information
    groups = open_groups_file()
    projects = open_projects_file()
    users = open_users_file()

    # Rewriting projects to retrieve objects by ID more efficiently
    for i, _ in enumerate(projects):
        rewritten_projects[projects[i]["id"]] = projects[i]

    for i, _ in enumerate(groups):
        rewritten_groups[groups[i]["id"]] = groups[i]

    for i, _ in enumerate(users):
        rewritten_users[users[i]["id"]] = users[i]

    # If there are groups selected in UI
    if not groups_to_stage[0] == "":
        # Stage ALL
        if groups_to_stage[0] == "all" or len(groups_to_stage) == len(groups):
            for i, _ in enumerate(projects):
                obj = get_project_metadata(projects[i])
                members = []
                for member in projects_api.get_members(
                        int(projects[i]["id"]), b.config.source_host, b.config.source_token):
                    append_member_to_members_list(members, member, dry_run)
                obj["members"] = members
                staged_projects.append(obj)

            for g in groups:
                b.log.info("{0}Staging group {1} (ID: {2})".format(
                    get_dry_log(dry_run), g["full_path"], g["id"]))
                g.pop("projects", None)
                staged_groups.append(g)

            for user in users:
                staged_users.append(user)
        # CLI range input
        elif re.search(r"\d+-\d+", groups_to_stage[0]) is not None:
            match = (re.search(r"\d+-\d+", groups_to_stage[0])).group(0)
            start = int(match.split("-")[0])
            if start != 0:
                start -= 1
            end = int(match.split("-")[1])
            for i in range(start, end):
                # Retrieve group object from groups.json
                append_data(groups[i], groups_to_stage, p_range=range(
                    start, end), dry_run=dry_run)
        # Random selection
        else:
            for i, _ in enumerate(groups_to_stage):
                # Hacky check for id or project name by explicitly checking
                # variable type
                try:
                    if (isinstance(int(groups_to_stage[i]), int)):
                        # Retrieve group object from groups.json
                        group = rewritten_groups[int(groups_to_stage[i])]
                except ValueError:
                    # Iterate over original groups.json file
                    for j, _ in enumerate(groups):
                        if groups[j]["full_path"] == groups_to_stage[i]:
                            group = groups[j]
                append_data(group, groups_to_stage, dry_run=dry_run)
    return remove_dupes(staged_projects), remove_dupes(
        staged_users), remove_dupes(staged_groups)


def append_data(group, groups_to_stage, p_range=0, dry_run=True):
    # Append all group projects to staged projects
    for project in group["projects"]:
        project_members = []
        obj = get_project_metadata(project)
        # Append all project members to staged users
        for project_member in projects_api.get_members(
                int(project["id"]), b.config.source_host, b.config.source_token):
            append_member_to_members_list(
                project_members, project_member, dry_run)
        obj["members"] = project_members
        b.log.info("{0}Staging project {1} (ID: {2})".format(
            get_dry_log(dry_run), obj["path_with_namespace"], obj["id"]))
        staged_projects.append(obj)

    b.log.info("{0}Staging group {1} (ID: {2}) [{3}/{4}]".format(get_dry_log(
        dry_run), group["full_path"], group["id"], len(staged_groups) + 1, len(p_range) if p_range else len(groups_to_stage)))
    group.pop("projects", None)
    staged_groups.append(group)

    # Append all group members to staged users
    for member in group["members"]:
        append_member_to_members_list([], member, dry_run)


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
    with open("%s/data/staged_groups.json" % b.app_path, "wb") as f:
        f.write(json.dumps(remove_dupes(staged_groups), indent=4))
    with open("%s/data/staged_projects.json" % b.app_path, "wb") as f:
        f.write(json.dumps(remove_dupes(staged_projects), indent=4))
    if not skip_users:
        with open("%s/data/staged_users.json" % b.app_path, "wb") as f:
            f.write(json.dumps(remove_dupes(staged_users), indent=4))


def append_member_to_members_list(members_list, member, dry_run=True):
    """
        Appends the members found in the /members endpoint to the staged asset object

        params: rewritten_users: object containing the various users from the instance
        params: staged_users:  object containing the specific users to be staged
        params: member_users: object containing the specific members of the group or project
        params: rewritten_users: object containing the specific member to be added to the group or project
    """
    if isinstance(member, dict):
        if member.get("id", None) is not None and member["username"] != "root":
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
