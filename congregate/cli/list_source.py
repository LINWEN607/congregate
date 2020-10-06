import os

from congregate.helpers.base_class import BaseClass
from congregate.helpers.processes import start_multi_process_with_args
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.projects import ProjectsClient

from congregate.migration.bitbucket.projects import ProjectsClient as BitBucketProjects
from congregate.migration.bitbucket.users import UsersClient as BitBucketUsers
from congregate.migration.bitbucket.repos import ReposClient as BitBucketRepos
from congregate.migration.bitbucket.groups import GroupsClient as BitBucketGroups

from congregate.migration.github.repos import ReposClient as GitHubRepos
from congregate.migration.github.orgs import OrgsClient as GitHubOrgs
from congregate.migration.github.users import UsersClient as GitHubUsers

from congregate.migration.jenkins.base import JenkinsClient as JenkinsData
from congregate.migration.teamcity.base import TeamcityClient as TeamcityData

from congregate.helpers.mdbc import MongoConnector

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


def list_bitbucket_data():
    users = BitBucketUsers()
    projects = BitBucketProjects()
    repos = BitBucketRepos()
    groups_client = BitBucketGroups()

    groups = groups_client.retrieve_group_info()

    projects.retrieve_project_info(groups=groups)
    repos.retrieve_repo_info(groups=groups)
    users.retrieve_user_info()


def list_github_data():
    mongo = MongoConnector()
    repos = GitHubRepos()
    orgs = GitHubOrgs()
    users = GitHubUsers()

    users.retrieve_user_info()
    repos.retrieve_repo_info()
    orgs.retrieve_org_info()
    

    mongo.dump_collection_to_file("projects", f"{b.app_path}/data/project_json.json")
    mongo.dump_collection_to_file("groups", f"{b.app_path}/data/groups.json")
    mongo.dump_collection_to_file("users", f"{b.app_path}/data/users.json")


def list_jenkins_data():
    data = JenkinsData()

    data.retrieve_jobs_with_scm_info()


def list_teamcity_data():
    data = TeamcityData()

    data.retrieve_jobs_with_vcs_info()


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
    ci_src_type = b.config.ci_source_type
    staged_files = ["staged_projects", "staged_groups", "staged_users"]

    if ci_src_type == "jenkins":
        list_jenkins_data()
        staged_files.append("jenkins_jobs")

    if ci_src_type == "teamcity":
        list_teamcity_data()
        staged_files.append("teamcity_jobs")

    if src_type == "bitbucket server":
        list_bitbucket_data()
    elif src_type == "gitlab":
        list_gitlab_data()
    elif src_type == "github":
        list_github_data()
    else:
        b.log.warning("Cannot list from source {}".format(src_type))
        exit()

    for f in staged_files:
        write_empty_file(f)


if __name__ == "__main__":
    list_data()
