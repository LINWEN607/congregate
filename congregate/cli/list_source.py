import os

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.projects import ProjectsClient

from congregate.migration.bitbucket.projects import ProjectsClient as BitBucketProjects
from congregate.migration.bitbucket.users import UsersClient as BitBucketUsers
from congregate.migration.bitbucket.repos import ReposClient as BitBucketRepos


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

    for filename in ["staged_projects", "staged_groups", "staged_users"]:
        write_empty_file(filename)


def list_bitbucket_data():
    users = BitBucketUsers()
    projects = BitBucketProjects()
    repos = BitBucketRepos()

    projects.retrieve_project_info()
    repos.retrieve_repo_info()
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

    staged_files = ["staged_projects", "staged_groups", "staged_users"]

    for filename in staged_files:
        write_empty_file(filename)


if __name__ == "__main__":
    list_data()
