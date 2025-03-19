import os
import sys
import click
from time import sleep

from celery import shared_task

from gitlab_ps_utils.misc_utils import strip_netloc
from gitlab_ps_utils.string_utils import deobfuscate

from congregate.helpers.base_class import BaseClass
from congregate.helpers.conf import Config
from congregate.helpers.utils import is_dot_com
from congregate.helpers.celery_utils import find_pending_tasks
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

from congregate.migration.ado.projects import ProjectsClient as AdoProjects
from congregate.migration.ado.groups import GroupsClient as AdoGroups
from congregate.migration.ado.users import UsersClient as AdoUsers
from congregate.migration.ado.api.projects import ProjectsApi as AdoProjectsApi

from congregate.migration.jenkins.base import JenkinsClient as JenkinsData
from congregate.migration.teamcity.base import TeamcityClient as TeamcityData

from congregate.helpers.congregate_mdbc import CongregateMongoConnector, mongo_connection

LIST_TASKS = [
    'list_data',
    'retrieve-bbs-users',
    'retrieve-bbs-projects',
    'retrieve-bbs-repos',
    'retrieve-bbs-user-groups',
    'retrieve-gh-users',
    'retrieve-gh-orgs',
    'retrieve-gh-repos',
    'retrieve-gl-users',
    'retrieve-gl-groups',
    'retrieve-gl-projects',
    'retrieve-ado-users',
    'retrieve-ado-projects',
    'retrieve-ado-groups'
]

class ListClient(BaseClass):
    def __init__(
        self,
        processes=None,
        partial=False,
        skip_users=False,
        skip_groups=False,
        skip_group_members=False,
        skip_projects=False,
        skip_project_members=False,
        skip_ci=False,
        src_instances=False,
        subset=False,
        skip_archived_projects=False,
        only_specific_projects=None
    ):
        super().__init__()
        self.processes = processes
        self.partial = partial
        self.skip_users = skip_users
        self.skip_groups = skip_groups
        self.skip_group_members = skip_group_members
        self.skip_projects = skip_projects
        self.skip_project_members = skip_project_members
        self.skip_ci = skip_ci
        self.src_instances = src_instances
        self.subset = subset
        self.skip_archived_projects = skip_archived_projects
        self.only_specific_projects = only_specific_projects

    def list_gitlab_data(self):
        """
            List the projects information, and Retrieve user info, group info from source instance.
            File-based - Save all projects, groups, and users information into mongodb and json file.
        """
        mongo, p, g, u = self.mongo_init()
        host = self.config.source_host
        token = self.config.source_token

        if not self.skip_users:
            users = UsersClient()
            users.retrieve_user_info(host, token, processes=self.processes)
            if not self.config.direct_transfer:
                mongo.dump_collection_to_file(
                    u, f"{self.app_path}/data/users.json")

        # Lists all groups and group projects
        if not self.skip_groups:
            groups = GroupsClient()
            groups.skip_group_members = self.skip_group_members
            groups.skip_project_members = self.skip_project_members
            groups.retrieve_group_info(host, token, processes=self.processes)
            if not self.config.direct_transfer:
                mongo.dump_collection_to_file(
                    g, f"{self.app_path}/data/groups.json")

        # Listing groups on gitlab.com will also list their projects
        # Listing on-prem includes personal projects
        if not self.skip_projects and not is_dot_com(host):
            projects = ProjectsClient()
            projects.skip_project_members = self.skip_project_members
            projects.retrieve_project_info(
                host, token, processes=self.processes)

        # When to dump listed projects
        if not self.skip_projects and not self.config.direct_transfer:
            mongo.dump_collection_to_file(
                p, f"{self.app_path}/data/projects.json")

        mongo.close_connection()

    def list_bitbucket_data(self):
        mongo, p, g, u = self.mongo_init(subset=self.subset)
        if not self.skip_group_members or not self.skip_project_members:
            user_groups = BitBucketGroups().retrieve_group_info()
        if not self.skip_users:
            users = BitBucketUsers()
            users.retrieve_user_info(processes=self.processes)
            mongo.dump_collection_to_file(
                u, f"{self.app_path}/data/users.json")
        if not self.skip_groups:
            projects = BitBucketProjects(subset=self.subset)
            if not self.skip_group_members:
                projects.set_user_groups(user_groups)
            projects.retrieve_project_info(processes=self.processes, skip_archived_projects=self.skip_archived_projects)
            mongo.dump_collection_to_file(
                g, f"{self.app_path}/data/groups.json")
            # Save listed BB Server parent projects
            if self.subset:
                mongo.dump_collection_to_file(
                    p, f"{self.app_path}/data/projects.json")
        if not self.skip_projects:
            repos = BitBucketRepos(subset=self.subset)
            if not self.skip_project_members:
                repos.set_user_groups(user_groups)
            repos.retrieve_repo_info(processes=self.processes, skip_archived_projects=self.skip_archived_projects)
            mongo.dump_collection_to_file(
                p, f"{self.app_path}/data/projects.json")
            # Save listed BB Server parent projects
            if self.subset:
                mongo.dump_collection_to_file(
                    g, f"{self.app_path}/data/groups.json")
        mongo.close_connection()

    def list_github_data(self):
        mongo, p, g, u = self.mongo_init()

        if not self.src_instances:
            host = self.config.source_host
            token = self.config.source_token
            app = self.app_path
            if not self.skip_users:
                users = GitHubUsers(
                    host, token, self.config.source_username, self.config.source_password)
                users.retrieve_user_info(processes=self.processes)
                mongo.dump_collection_to_file(u, f"{app}/data/users.json")
            if not self.skip_groups:
                orgs = GitHubOrgs(host, token)
                orgs.retrieve_org_info(processes=self.processes)
                mongo.dump_collection_to_file(g, f"{app}/data/groups.json")
            if not self.skip_projects:
                repos = GitHubRepos(host, token)
                repos.retrieve_repo_info(processes=self.processes)
                mongo.dump_collection_to_file(p, f"{app}/data/projects.json")
        else:
            for _, single_source in enumerate(
                    self.config.list_multiple_source_config("github_source")):
                host = strip_netloc(single_source.get('src_hostname', ""))
                token = deobfuscate(single_source.get('src_access_token', ""))
                app = self.app_path
                if not self.skip_users:
                    users = GitHubUsers(host, token, single_source.get(
                        'src_username'), deobfuscate(single_source.get('src_password')))
                    users.retrieve_user_info(processes=self.processes)
                    mongo.dump_collection_to_file(u, f"{app}/data/{u}.json")
                if not self.skip_groups:
                    orgs = GitHubOrgs(host, token)
                    orgs.retrieve_org_info(processes=self.processes)
                    mongo.dump_collection_to_file(g, f"{app}/data/{g}.json")
                if not self.skip_projects:
                    repos = GitHubRepos(host, token)
                    repos.retrieve_repo_info(processes=self.processes)
                    mongo.dump_collection_to_file(p, f"{app}/data/{p}.json")
        mongo.close_connection()

    def list_azure_devops_data(self):
        mongo, p, g, u = self.mongo_init()

        if self.only_specific_projects:
            projects_list = []

            project_ids = self.only_specific_projects.split(",")

            for project_id in project_ids:
                project_response = AdoProjectsApi().get_project(project_id)
                if project_response.status_code == 200:
                    project_data = project_response.json()
                    data = {
                        "id": project_data.get("id"),
                        "name": project_data.get("name"),
                        "description": project_data.get("description", ""),
                        "url": project_data.get("url"),
                        "state": project_data.get("state"),
                        "revision": project_data.get("revision"),
                        "visibility": project_data.get("visibility"),
                        "lastUpdateTime": project_data.get("lastUpdateTime")
                    }
                    projects_list.append(data)
                else:
                    raise Exception(f"Failed to retrieve project '{project_id}' with status code {project_response.status_code}")

            # Find only projects with =<1 repo ( = project in GitLab)
            if not self.skip_projects:
                projects = AdoProjects()
                projects.retrieve_project_info(processes=self.processes, projects_list=projects_list)
                mongo.dump_collection_to_file(
                    p, f"{self.app_path}/data/projects.json")

            # Find ADO projects with >1 repos ( = group in GitLab)
            if not self.skip_groups:
                groups = AdoGroups()
                groups.retrieve_group_info(processes=self.processes, projects_list=projects_list)
                mongo.dump_collection_to_file(
                    g, f"{self.app_path}/data/groups.json")

        else:

            # Find only projects with =<1 repo ( = project in GitLab)
            if not self.skip_projects:
                projects = AdoProjects()
                projects.retrieve_project_info(processes=self.processes)
                mongo.dump_collection_to_file(
                    p, f"{self.app_path}/data/projects.json")

            # Find ADO projects with >1 repos ( = group in GitLab)
            if not self.skip_groups:
                groups = AdoGroups()
                groups.retrieve_group_info(processes=self.processes)
                mongo.dump_collection_to_file(
                    g, f"{self.app_path}/data/groups.json")
                
        if not self.skip_users:
            users = AdoUsers()
            users.retrieve_user_info(processes=self.processes)
            mongo.dump_collection_to_file(
                u, f"{self.app_path}/data/users.json")

        mongo.close_connection()

    def list_jenkins_data(self):
        mongo = CongregateMongoConnector()
        for i, single_jenkins_ci_source in enumerate(
                self.config.list_ci_source_config("jenkins_ci_source")):
            collection_name = f"jenkins-{single_jenkins_ci_source.get('jenkins_ci_src_hostname').split('//')[-1]}"
            data = JenkinsData(single_jenkins_ci_source.get("jenkins_ci_src_hostname"), single_jenkins_ci_source.get(
                "jenkins_ci_src_username"), deobfuscate(single_jenkins_ci_source.get("jenkins_ci_src_access_token")))
            data.retrieve_jobs_with_scm_info(i)
            mongo.dump_collection_to_file(
                collection_name, f"{self.app_path}/data/jenkins-{i}.json")

    def list_teamcity_data(self):
        mongo = CongregateMongoConnector()
        for i, single_teamcity_ci_source in enumerate(
                self.config.list_ci_source_config("teamcity_ci_source")):
            collection_name = f"teamcity-{single_teamcity_ci_source.get('tc_ci_src_hostname').split('//')[-1]}"
            data = TeamcityData(single_teamcity_ci_source.get("tc_ci_src_hostname"), single_teamcity_ci_source.get(
                "tc_ci_src_username"), deobfuscate(single_teamcity_ci_source.get("tc_ci_src_access_token")))
            data.retrieve_jobs_with_scm_info(i)
            mongo.dump_collection_to_file(
                collection_name, f"{self.app_path}/data/teamcity-{i}.json")

    def write_empty_file(self, filename):
        """
            Write an empty json file containing an empty list, it's used to make sure a file is present in the filesystem

            :param: filename: (str) json file
        """
        if not os.path.isfile(f"{self.app_path}/data/{filename}.json"):
            with open(f"{self.app_path}/data/{filename}.json", "w") as f:
                f.write("[]")

    def list_data(self, as_task=False):
        if as_task:
            watch_task = watch_list_status.delay()
        src_type = self.config.source_type or "unknown"
        staged_files = ["staged_projects", "staged_groups", "staged_users"]

        if self.config.list_ci_source_config("jenkins_ci_source") and not self.skip_ci:
            self.log.info("Listing data from Jenkins CI source")
            self.list_jenkins_data()
            staged_files.append("jenkins_jobs")

        if self.config.list_ci_source_config("teamcity_ci_source") and not self.skip_ci:
            self.log.info("Listing data from TeamCity CI source")
            self.list_teamcity_data()
            staged_files.append("teamcity_jobs")

        self.log.info(
            f"Listing data from {src_type} source type - {self.config.source_host}")
        # In case one skips users/groups/projects on first list
        self.initialize_list_files()
        if src_type == "bitbucket server":
            self.list_bitbucket_data()
        elif src_type == "gitlab":
            self.list_gitlab_data()
        elif src_type == "github":
            self.list_github_data()
        elif src_type == "azure devops":
            self.list_azure_devops_data()
        else:
            self.log.warning(
                f"Cannot list from {src_type} source type - {self.config.source_host}")
            raise Exception

        for f in staged_files:
            self.write_empty_file(f)
        if as_task:
            return watch_task.id

    def initialize_list_files(self):
        objects = ["users", "groups", "projects"]
        if self.config.source_type == "bitbucket server":
            objects.append("bb_groups")
        for o in objects:
            file_path = f"{self.app_path}/data/{o}.json"
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write("[]")

    def mongo_init(self, subset=False):
        mongo = CongregateMongoConnector()
        src_hostname = strip_netloc(self.config.source_host)
        p = f"projects-{src_hostname}"
        g = f"groups-{src_hostname}"
        u = f"users-{src_hostname}"
        if not self.partial:
            self.log.info("Dropping database collections")
            if not self.skip_projects or subset:
                mongo.drop_collection(p)
            if not self.skip_groups or subset:
                mongo.drop_collection(g)
            if not self.skip_users:
                mongo.drop_collection(u)
        return mongo, p, g, u


@shared_task(name='list_data')
def list_data(partial=False, skip_users=False, skip_groups=False, skip_group_members=False,
              skip_projects=False, skip_project_members=False, skip_ci=False, 
              src_instances=False, subset=False):
    client = ListClient(partial=partial, skip_users=skip_users, skip_groups=skip_groups, skip_group_members=skip_group_members,
              skip_projects=skip_projects, skip_project_members=skip_project_members, skip_ci=skip_ci, 
              src_instances=src_instances, subset=subset)
    return client.list_data(as_task=True)

@shared_task(name='watch-for-list-to-complete')
@mongo_connection
def watch_list_status(mongo=None):
    b = BaseClass()
    assets = ['users', 'groups', 'projects']
    src_hostname = strip_netloc(b.config.source_host)
    sleep(5)
    open_jobs = [x for x in find_pending_tasks(LIST_TASKS)]
    b.log.info(f"Open jobs: {open_jobs}")
    time_elapsed = 0
    while len(open_jobs) > 0:
        if time_elapsed > b.config.list_task_timeout:
            b.log.info(f"List tasks still running past configured timeout of {b.config.list_task_timeout} seconds. Dumping data retrieved so far.")
            break
        b.log.info("Waiting for list to finish")
        b.log.info(f"Open jobs: {open_jobs}")
        sleep(5)
        time_elapsed += 5
        open_jobs = [x for x in find_pending_tasks(LIST_TASKS)]
    for asset in assets:
        b.log.info(f"Saving {asset} to {b.app_path}/data/{asset}.json")
        mongo.dump_collection_to_file(
            f"{asset}-{src_hostname}", f"{b.app_path}/data/{asset}.json")
