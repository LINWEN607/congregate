"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

import json
import re

from congregate.helpers.base_class import BaseClass
from congregate.helpers.migrate_utils import is_top_level_group
from congregate.helpers.misc_utils import get_dry_log, remove_dupes
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi

projects_api = ProjectsApi()
groups_api = GroupsApi()
b = BaseClass()

# TODO: Break down into separate staging areas
# Stage users, groups and projects
# Function definition is here
# groups_to_stage = []
def stage_groups(groups_to_stage, dry_run=True, skip_users=False):
    """
        Stage all the groups from the source instance

        :param: groups_to_stage: (dict) the staged groups objects
        :param: dry_run (bool) If true, it will only build the staging data lists
    """
    staged_groups, staged_users, staged_projects = build_staging_data(
        groups_to_stage, dry_run)
    if not dry_run:
        write_staging_files(staged_groups, staged_users,
                            staged_projects, skip_users=skip_users)

def build_staging_data(groups_to_stage, dry_run=True):
    """
        Stage all the data including project, groups and users from the source instance

        :param: groups_to_stage: (dict) the staged projects objects
        :param: dry_run (bool) If true, it will only build the staging data lists.
    """
    # Initilazing the groups, users and projects
    staged_groups = []
    staged_users = []
    staged_projects = []

    # Loading projects information
    groups = open_groups_file()
    projects = open_projects_file()
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
    # if the groups are not empty, stage all the projects and users
    if not groups_to_stage[0] == "":
        if groups_to_stage[0] == "all" or groups_to_stage[0] == ".":
            print ("call stage_groups.build_staging_data(), the parameter is all\n")
            # Stage ALL groups
            for g in groups:
                # get_all_group_members
                b.log.info("Staging {0} {1} (ID: {2})".format(
                    "top-level group" if is_top_level_group(g) else "sub-group", g["full_path"], g["id"]))
                staged_groups.append(g)
            # Stage ALL projects
            for i, _ in enumerate(projects):
                obj = get_project_metadata(projects[i])
                members = []
                for member in projects_api.get_members(
                        int(projects[i]["id"]), b.config.source_host, b.config.source_token):
                    append_member_to_members_list(
                        rewritten_users, staged_users, members, member)
                obj["members"] = members
                staged_projects.append(obj)
            # Stage ALL users
            for user in users:
                staged_users.append(user)    
        # Based on ID name 
        else:
            for i, _ in enumerate(groups_to_stage):
                # Hacky check for id or project name by explicitly checking
                # variable type
                try:
                    if (isinstance(int(groups_to_stage[i]), int)):
                        key = groups_to_stage[i]
                        print ('the value of key: '+ (key))
                        # Retrieve object from better formatted object
                        group = rewritten_groups[int(key)]
                except ValueError:
                    # Iterate over original project_json.json file
                    for j, _ in enumerate(projects):
                        if groups[j]["name"] == groups_to_stage[i]:
                            group = projects[j]  
                staged_groups.append(group)
                # Get all the users belong to the group
                members = []
                for member in groups_api.get_all_group_members(
                        int(group["id"]), b.config.source_host, b.config.source_token):
                    append_member_to_members_list(
                        rewritten_users, staged_users, members, member)
                # Get all the stage projects under the group
                for project in groups_api.get_all_group_projects(
                    int(group["id"]), b.config.source_host, b.config.source_token):
                    obj = get_project_metadata(project)
                    obj["members"] = members
                    staged_projects.append(obj)
    # Groups are empty, stage all projects and users
    else:
        staged_groups = []


    return remove_dupes(staged_groups), remove_dupes(
        staged_users), remove_dupes(staged_projects)


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


def write_staging_files(staged_groups, staged_users,
                            staged_projects, skip_users=False):
    """
        Write all staged projects, users and groups objects into JSON files

        :param: staging: (dict) staged projects
        :param: staged_users:(dict) staged users
        :param: staged_groups: (dict) staged groups
    """
    with open("%s/data/staged_groups.json" % b.app_path, "wb") as f:
        f.write(json.dumps(staged_groups, indent=4))
    with open("%s/data/staged_projects.json" % b.app_path, "wb") as f:
        f.write(json.dumps(staged_projects, indent=4))
    if not skip_users:
        with open("%s/data/staged_users.json" % b.app_path, "wb") as f:
            f.write(json.dumps(staged_users, indent=4))


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


def get_group_metadata(group):
    """
        Get the object data providing project information

        :param project: (str) project information
        :return: obj object
    """
    obj = {

    }
    return obj

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
