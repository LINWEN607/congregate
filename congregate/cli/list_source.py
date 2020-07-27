import os

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.projects import ProjectsClient

from congregate.migration.bitbucket.projects import ProjectsClient as BitBucketProjects
from congregate.migration.bitbucket.users import UsersClient as BitBucketUsers
from congregate.migration.bitbucket.repos import ReposClient as BitBucketRepos

from congregate.migration.github.orgs import OrgsClient as GitHubOrgs
from congregate.migration.github.users import UsersClient as GitHubUsers

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


def list_github_data():
    orgs = GitHubOrgs()
    users = GitHubUsers()
    orgs.retrieve_org_info()
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
    src_type = b.config.source_type
    if src_type == "Bitbucket Server":
        list_bitbucket_data()
    elif src_type == "GitLab":
        list_gitlab_data()
    elif src_type == "GitHub":
        list_github_data()
    else:
        b.log.warning("Cannot list from source {}".format(src_type))
        exit()

    staged_files = ["staged_projects", "staged_groups", "staged_users"]

    for filename in staged_files:
        write_empty_file(filename)


if __name__ == "__main__":
    list_data()
