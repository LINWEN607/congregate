import os

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import write_json_yield_to_file
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.bitbucket.users import UsersClient as BitBucketUsers
from congregate.migration.bitbucket.repos import ReposClient as BitBucketRepos
from congregate.migration.bitbucket.api.projects import ProjectsApi as BitBucketProjectsApi


b = BaseClass()


def list_gitlab_data():
    """
        List the projects information, and Retrieve user info, group info from source instance.
    """
    groups = GroupsClient()
    users = UsersClient()
    projects = ProjectsClient()

    b.log.info("Listing data from source {}".format(b.config.source_host))
    projects.retrieve_project_info(b.config.source_host, b.config.source_token)
    groups.retrieve_group_info(b.config.source_host, b.config.source_token)
    users.retrieve_user_info(b.config.source_host, b.config.source_token)

    for filename in ["stage", "staged_groups", "staged_users"]:
        write_empty_file(filename)


def list_bitbucket_data():
    users = BitBucketUsers()
    projects = BitBucketProjectsApi()
    repos = BitBucketRepos()

    repos.retrieve_repo_info()
    write_json_yield_to_file(
        "%s/data/groups.json" % b.app_path,
        projects.get_all_projects,
        b.config.external_source_url,
        b.config.external_user_token
    )
    users.retrieve_user_info()


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
