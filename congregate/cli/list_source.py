import json
import os
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present, remove_dupes, write_json_yield_to_file
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.bitbucket.api.repos import ReposApi
from congregate.migration.bitbucket.api.users import UsersApi as BitBucketUsersApi
from congregate.migration.bitbucket.api.projects import ProjectsApi as BitBucketProjectsApi


b = BaseClass()


def list_gitlab_data():
    """
        List the projects information, and Retrieve user info, group info from source instance.
    """
    groups = GroupsClient()
    users = UsersClient()
    projects_api = ProjectsApi()
    groups_api = GroupsApi()
    b.log.info("Listing projects from source {}".format(b.config.source_host))

    projects = []

    if b.config.src_parent_group_path:
        projects = list(groups_api.get_all_group_projects(
            b.config.src_parent_id, b.config.source_host, b.config.source_token, with_shared=False))
    else:
        projects = list(projects_api.get_all_projects(
            b.config.source_host, b.config.source_token))

    with open("%s/data/project_json.json" % b.app_path, "wb") as f:
        json.dump(remove_dupes(projects), f, indent=4)

    for project in projects:
        if is_error_message_present(project):
            b.log.error(
                "Failed to list project with response: {}".format(project))
        else:
            b.log.info(u"[ID: {0}] {1}: {2}".format(
                project["id"], project["name"], project["description"]))

    groups.retrieve_group_info(
        b.config.source_host, b.config.source_token, quiet=True)
    users.retrieve_user_info(b.config.source_host,
                             b.config.source_token, quiet=True)

    for filename in ["stage", "staged_groups", "staged_users"]:
        write_empty_file(filename)


def list_bitbucket_data():
    users = BitBucketUsersApi()
    projects = BitBucketProjectsApi()
    repos = ReposApi()

    write_json_yield_to_file(
        "%s/data/project_json.json" % b.app_path,
        repos.get_all_repos,
        b.config.external_source_url,
        b.config.external_user_token
    )

    write_json_yield_to_file(
        "%s/data/users.json" % b.app_path,
        users.get_all_users,
        b.config.external_source_url,
        b.config.external_user_token
    )

    write_json_yield_to_file(
        "%s/data/groups.json" % b.app_path,
        projects.get_all_projects,
        b.config.external_source_url,
        b.config.external_user_token
    )


def write_empty_file(filename):
    """
        Write an empty json file containing an empty list, it's used to make sure a file is present in the filesystem

        :param: filename: (str) json file
    """
    if not os.path.isfile("%s/data/%s.json" % (b.app_path, filename)):
        with open("%s/data/%s.json" % (b.app_path, filename), "w") as f:
            f.write("[]")


def list_data():
    ext_src = b.config.external_source_url
    src = b.config.source_host
    if ext_src and "gitlab" not in ext_src.lower():
        list_bitbucket_data()
    elif src:
        list_gitlab_data()
    else:
        b.log.warning(
            "Cannot list from source (External: {0}, GitLab: {1})".format(ext_src, src))
        exit()

    staged_files = ["stage", "staged_groups", "staged_users"]

    for filename in staged_files:
        write_empty_file(filename)


if __name__ == "__main__":
    list_data()
