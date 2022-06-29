import os
import sys

from gitlab_ps_utils.misc_utils import strip_netloc
from gitlab_ps_utils.string_utils import deobfuscate

from congregate.helpers.base_class import BaseClass
from congregate.helpers.utils import is_dot_com
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


def list_gitlab_data(
        processes=None,
        partial=False,
        skip_users=False,
        skip_groups=False,
        skip_group_members=False,
        skip_projects=False,
        skip_project_members=False):
    """
        List the projects information, and Retrieve user info, group info from source instance.
    """
    mongo, p, g, u = mongo_init(partial=partial)
    host = b.config.source_host
    token = b.config.source_token

    if not skip_users:
        users = UsersClient()
        users.retrieve_user_info(host, token, processes=processes)
        mongo.dump_collection_to_file(u, f"{b.app_path}/data/users.json")

    if not skip_groups:
        groups = GroupsClient()
        groups.skip_group_members = skip_group_members
        groups.skip_project_members = skip_project_members
        groups.retrieve_group_info(host, token, processes=processes)
        mongo.dump_collection_to_file(g, f"{b.app_path}/data/groups.json")

    # When to list projects - Listing groups on gitlab.com will also list their projects
    if not skip_projects and not is_dot_com(host):
        projects = ProjectsClient()
        projects.skip_project_members = skip_project_members
        projects.retrieve_project_info(host, token, processes=processes)

    # When to dump listed projects
    if not skip_projects:
        mongo.dump_collection_to_file(p, f"{b.app_path}/data/projects.json")

    mongo.close_connection()


def list_bitbucket_data(
        processes=None,
        partial=False,
        skip_users=False,
        skip_groups=False,
        skip_projects=False):
    mongo, p, g, u = mongo_init(partial=partial)

    groups_client = BitBucketGroups()
    groups = groups_client.retrieve_group_info()
    if not skip_users:
        users = BitBucketUsers()
        users.retrieve_user_info(processes=processes)
        mongo.dump_collection_to_file(u, f"{b.app_path}/data/users.json")
    if not skip_groups:
        projects = BitBucketProjects()
        projects.set_user_groups(groups)
        projects.retrieve_project_info(processes=processes)
        mongo.dump_collection_to_file(g, f"{b.app_path}/data/groups.json")
    if not skip_projects:
        repos = BitBucketRepos()
        repos.set_user_groups(groups)
        repos.retrieve_repo_info(processes=processes)
        mongo.dump_collection_to_file(p, f"{b.app_path}/data/projects.json")

    mongo.close_connection()


def list_github_data(processes=None, partial=False, skip_users=False,
                     skip_groups=False, skip_projects=False, src_instances=False):
    mongo, p, g, u = mongo_init(partial=partial)

    if not src_instances:
        host = b.config.source_host
        token = b.config.source_token
        app = b.app_path
        if not skip_users:
            users = GitHubUsers(
                host, token, b.config.source_username, b.config.source_password)
            users.retrieve_user_info(processes=processes)
            mongo.dump_collection_to_file(u, f"{app}/data/users.json")
        if not skip_groups:
            orgs = GitHubOrgs(host, token)
            orgs.retrieve_org_info(processes=processes)
            mongo.dump_collection_to_file(g, f"{app}/data/groups.json")
        if not skip_projects:
            repos = GitHubRepos(host, token)
            repos.retrieve_repo_info(processes=processes)
            mongo.dump_collection_to_file(p, f"{app}/data/projects.json")
    else:
        for _, single_source in enumerate(
                b.config.list_multiple_source_config("github_source")):
            host = strip_netloc(single_source.get('src_hostname', ""))
            token = deobfuscate(single_source.get('src_access_token', ""))
            app = b.app_path
            if not skip_users:
                users = GitHubUsers(host, token, single_source.get(
                    'src_username'), deobfuscate(single_source.get('src_password')))
                users.retrieve_user_info(processes=processes)
                mongo.dump_collection_to_file(u, f"{app}/data/{u}.json")
            if not skip_groups:
                orgs = GitHubOrgs(host, token)
                orgs.retrieve_org_info(processes=processes)
                mongo.dump_collection_to_file(g, f"{app}/data/{g}.json")
            if not skip_projects:
                repos = GitHubRepos(host, token)
                repos.retrieve_repo_info(processes=processes)
                mongo.dump_collection_to_file(p, f"{app}/data/{p}.json")
    mongo.close_connection()


def list_jenkins_data():
    mongo = MongoConnector()
    for i, single_jenkins_ci_source in enumerate(
            b.config.list_ci_source_config("jenkins_ci_source")):
        collection_name = f"jenkins-{single_jenkins_ci_source.get('jenkins_ci_src_hostname').split('//')[-1]}"
        data = JenkinsData(single_jenkins_ci_source.get("jenkins_ci_src_hostname"), single_jenkins_ci_source.get(
            "jenkins_ci_src_username"), deobfuscate(single_jenkins_ci_source.get("jenkins_ci_src_access_token")))
        data.retrieve_jobs_with_scm_info(i)
        mongo.dump_collection_to_file(
            collection_name, f"{b.app_path}/data/jenkins-{i}.json")


def list_teamcity_data():
    mongo = MongoConnector()
    for i, single_teamcity_ci_source in enumerate(
            b.config.list_ci_source_config("teamcity_ci_source")):
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


def list_data(
        processes=None,
        partial=False,
        skip_users=False,
        skip_groups=False,
        skip_group_members=False,
        skip_projects=False,
        skip_project_members=False,
        skip_ci=False,
        src_instances=False):

    src_type = b.config.source_type or "unknown"
    staged_files = ["staged_projects", "staged_groups", "staged_users"]

    if b.config.list_ci_source_config("jenkins_ci_source") and not skip_ci:
        b.log.info("Listing data from Jenkins CI source")
        list_jenkins_data()
        staged_files.append("jenkins_jobs")

    if b.config.list_ci_source_config("teamcity_ci_source") and not skip_ci:
        b.log.info("Listing data from TeamCity CI source")
        list_teamcity_data()
        staged_files.append("teamcity_jobs")

    b.log.info(
        f"Listing data from {src_type} source type - {b.config.source_host}")
    if src_type == "bitbucket server":
        list_bitbucket_data(
            processes=processes,
            partial=partial,
            skip_users=skip_users,
            skip_groups=skip_groups,
            skip_projects=skip_projects)
    elif src_type == "gitlab":
        list_gitlab_data(
            processes=processes,
            partial=partial,
            skip_users=skip_users,
            skip_groups=skip_groups,
            skip_group_members=skip_group_members,
            skip_projects=skip_projects,
            skip_project_members=skip_project_members)
    elif src_type == "github":
        list_github_data(
            processes=processes,
            partial=partial,
            skip_users=skip_users,
            skip_groups=skip_groups,
            skip_projects=skip_projects,
            src_instances=src_instances)
    else:
        b.log.warning(
            f"Cannot list from {src_type} source type - {b.config.source_host}")
        sys.exit(os.EX_CONFIG)

    for f in staged_files:
        write_empty_file(f)


def mongo_init(partial=False, skip_users=False,
               skip_groups=False, skip_projects=False):
    mongo = MongoConnector()
    src_hostname = strip_netloc(b.config.source_host)
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
    return mongo, p, g, u


if __name__ == "__main__":
    list_data()
