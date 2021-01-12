import os

from congregate.helpers.base_class import BaseClass
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

from congregate.helpers.misc_utils import deobfuscate, strip_protocol

b = BaseClass()


def list_gitlab_data(skip_users=False, skip_groups=False, skip_projects=False):
    """
        List the projects information, and Retrieve user info, group info from source instance.
    """
    if not skip_users:
        users = UsersClient()
        users.retrieve_user_info(b.config.source_host, b.config.source_token)
    if not skip_groups:
        groups = GroupsClient()
        groups.retrieve_group_info(b.config.source_host, b.config.source_token)
    if not skip_projects:
        projects = ProjectsClient()
        projects.retrieve_project_info(
            b.config.source_host, b.config.source_token)


def list_bitbucket_data(skip_users=False, skip_groups=False, skip_projects=False):
    if not skip_users:
        users = BitBucketUsers()
        users.retrieve_user_info()
    if not skip_groups and not skip_projects:
        projects = BitBucketProjects()
        groups_client = BitBucketGroups()
        repos = BitBucketRepos()
        groups = groups_client.retrieve_group_info()
        projects.retrieve_project_info(groups=groups)
        repos.retrieve_repo_info(groups=groups)


def list_github_data(processes=None, partial=False, skip_users=False, skip_groups=False, skip_projects=False, src_instances=False):
    mongo = MongoConnector()
    src_hostname = strip_protocol(b.config.source_host)
    p = f"projects-{src_hostname}"
    g = f"groups-{src_hostname}"
    u = f"users-{src_hostname}"
    if not partial:
        b.log.info("Dropping database collections")
        if not skip_projects:
            mongo.drop_collection(p)
        if not skip_groups:
            mongo.drop_collection(g)
        if not skip_users:
            mongo.drop_collection(u)
    if not src_instances:
        if not skip_users:
            users = GitHubUsers(b.config.source_host, b.config.source_token,
                                b.config.source_username, b.config.source_password)
            users.retrieve_user_info(processes=processes)
            mongo.dump_collection_to_file(u, f"{b.app_path}/data/users.json")
        if not skip_groups:
            orgs = GitHubOrgs(b.config.source_host, b.config.source_token)
            orgs.retrieve_org_info(processes=processes)
            mongo.dump_collection_to_file(g, f"{b.app_path}/data/groups.json")
        if not skip_projects:
            repos = GitHubRepos(b.config.source_host, b.config.source_token)
            repos.retrieve_repo_info(processes=processes)
            mongo.dump_collection_to_file(
                p, f"{b.app_path}/data/projects.json")
    else:
        for _, single_source in enumerate(b.config.list_multiple_source_config("github_source")):
            src_hostname = strip_protocol(
                single_source.get('src_hostname', ""))
            if not skip_users:
                users = GitHubUsers(single_source.get('src_hostname'),
                                    deobfuscate(single_source.get(
                                        'src_access_token')),
                                    single_source.get('src_username'),
                                    deobfuscate(single_source.get('src_password')))
                users.retrieve_user_info(processes=processes)
                mongo.dump_collection_to_file(u, f"{b.app_path}/data/{u}.json")
            if not skip_groups:
                orgs = GitHubOrgs(single_source.get('src_hostname'), deobfuscate(
                    single_source.get('src_access_token')))
                orgs.retrieve_org_info(processes=processes)
                mongo.dump_collection_to_file(g, f"{b.app_path}/data/{g}.json")
            if not skip_projects:
                repos = GitHubRepos(single_source.get('src_hostname'), deobfuscate(
                    single_source.get('src_access_token')))
                repos.retrieve_repo_info(processes=processes)
                mongo.dump_collection_to_file(p, f"{b.app_path}/data/{p}.json")
    mongo.close_connection()


def list_jenkins_data():
    mongo = MongoConnector()
    for i, single_jenkins_ci_source in enumerate(b.config.list_ci_source_config("jenkins_ci_source")):
        collection_name = f"jenkins-{single_jenkins_ci_source.get('jenkins_ci_src_hostname').split('//')[-1]}"
        data = JenkinsData(single_jenkins_ci_source.get("jenkins_ci_src_hostname"), single_jenkins_ci_source.get(
            "jenkins_ci_src_username"), deobfuscate(single_jenkins_ci_source.get("jenkins_ci_src_access_token")))
        data.retrieve_jobs_with_scm_info(i)
        mongo.dump_collection_to_file(
            collection_name, f"{b.app_path}/data/jenkins-{i}.json")


def list_teamcity_data():
    mongo = MongoConnector()
    for i, single_teamcity_ci_source in enumerate(b.config.list_ci_source_config("teamcity_ci_source")):
        collection_name = f"teamcity-{single_teamcity_ci_source.get('tc_ci_src_hostname').split('//')[-1]}"
        data = TeamcityData(single_teamcity_ci_source.get("tc_ci_src_hostname"), single_teamcity_ci_source.get(
            "tc_ci_src_username"), deobfuscate(single_teamcity_ci_source.get("tc_ci_src_access_token")))
        data.retrieve_jobs_with_vcs_info(i)
        mongo.dump_collection_to_file(
            collection_name, f"{b.app_path}/data/teamcity-{i}.json")


def write_empty_file(filename):
    """
        Write an empty json file containing an empty list, it's used to make sure a file is present in the filesystem

        :param: filename: (str) json file
    """
    if not os.path.isfile("%s/data/%s.json" % (b.app_path, filename)):
        with open("%s/data/%s.json" % (b.app_path, filename), "w") as f:
            f.write("[]")


def list_data(processes=None, partial=False, skip_users=False, skip_groups=False, skip_projects=False, skip_ci=False, src_instances=False):
    src_type = b.config.source_type
    staged_files = ["staged_projects", "staged_groups", "staged_users"]

    if b.config.list_ci_source_config("jenkins_ci_source") and not skip_ci:
        b.log.info("Listing data from Jenkins CI source")
        list_jenkins_data()
        staged_files.append("jenkins_jobs")

    if b.config.list_ci_source_config("teamcity_ci_source") and not skip_ci:
        b.log.info("Listing data from TeamCity CI source")
        list_teamcity_data()
        staged_files.append("teamcity_jobs")

    b.log.info(f"Listing data from {src_type} source")
    if src_type == "bitbucket server":
        list_bitbucket_data(skip_users=skip_users,
                            skip_projects=skip_projects, skip_groups=skip_groups)
    elif src_type == "gitlab":
        list_gitlab_data(skip_users=skip_users,
                         skip_projects=skip_projects, skip_groups=skip_groups)
    elif src_type == "github":
        list_github_data(processes=processes, partial=partial, skip_users=skip_users,
                         skip_projects=skip_projects, skip_groups=skip_groups, src_instances=src_instances)
    else:
        b.log.warning("Cannot list from source {}".format(src_type))
        exit()

    for f in staged_files:
        write_empty_file(f)


if __name__ == "__main__":
    list_data()
