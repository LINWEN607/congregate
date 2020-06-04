"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

import json
import re
from congregate.helpers.misc_utils import get_dry_log, remove_dupes
from congregate.helpers.migrate_utils import is_top_level_group
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.groups import GroupsApi

groups_api = GroupsApi()
b = BaseClass()

# TODO: Break down into separate staging areas
# Stage users, groups and projects

def stage_group(groups_to_stage, dry_run=True, skip_users=False):
    """
        Stage all the groups from the source instance

        :param: groups_to_stage: (dict) the staged groups objects
        :param: dry_run (bool) If true, it will only build the staging data lists
    """
    staged_projects, staged_users, staged_groups = build_staging_data(
        groups_to_stage, dry_run)
    if not dry_run:
        write_staging_files(staged_projects, staged_users,
                            staged_groups, skip_users=skip_users)


def build_staging_data(groups_to_stage, dry_run=True):
    """
        Stage all the data including project, groups and users from the source instance

        :param: projects_to_stage: (dict) the staged projects objects
        :param: dry_run (bool) dry_run (bool) If true, it will only build the staging data lists.
    """

    

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


def write_staging_files(staging, staged_users, staged_groups, skip_users=False):
    """
        Write all staged projects, users and groups objects into JSON files

        :param: staging: (dict) staged projects
        :param: staged_users:(dict) staged users
        :param: staged_groups: (dict) staged groups
    """
    with open("%s/data/stage.json" % b.app_path, "wb") as f:
        f.write(json.dumps(staging, indent=4))
    with open("%s/data/staged_groups.json" % b.app_path, "wb") as f:
        f.write(json.dumps(staged_groups, indent=4))
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