import json
import os
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.projects import ProjectsApi

groups = GroupsClient()
users = UsersClient()
projects_api = ProjectsApi()
b = BaseClass()


def list_projects():
    """
        List the projects information, and Retrieve user info, group info from source instance.
    """
    b.log.info("Listing projects from source {}:".format(b.config.source_host))

    projects = list(
        projects_api.get_all_projects(
            b.config.source_host,
            b.config.source_token))

    with open("%s/data/project_json.json" % b.app_path, "wb") as f:
        json.dump(projects, f, indent=4)

    for project in projects:
        b.log.info(
            u"[ID: {0}] {1}: {2}".format(
                project["id"],
                project["name"],
                project["description"]))

    groups.retrieve_group_info(
        b.config.source_host,
        b.config.source_token,
        quiet=True)
    users.retrieve_user_info(
        b.config.source_host,
        b.config.source_token,
        quiet=True)

    staged_files = ["stage", "staged_groups", "staged_users"]

    for filename in staged_files:
        write_empty_file(filename)


def write_empty_file(filename):
    """
        Write an empty json file containing an empty list, it's used to make sure a file is present in the filesystem

        :param: filename: (str) json file
    """
    if not os.path.isfile("%s/data/%s.json" % (b.app_path, filename)):
        with open("%s/data/%s.json" % (b.app_path, filename), "w") as f:
            f.write("[]")


if __name__ == "__main__":
    list_projects()
