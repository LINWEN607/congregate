from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import remove_dupes_but_take_higher_access, strip_netloc, is_error_message_present
from gitlab_ps_utils.dict_utils import dig
from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.migrate_utils import get_subset_list, check_list_subset_input_file_path
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.users import UsersClient
from congregate.migration.bitbucket.repos import ReposClient
from congregate.migration.bitbucket.api.groups import GroupsApi


class ProjectsClient(BaseClass):
    @classmethod
    def connect_to_mongo(cls):
        return MongoConnector()

    def __init__(self, subset=False):
        self.projects_api = ProjectsApi()
        self.users = UsersClient()
        self.repos = ReposClient()
        self.groups_api = GroupsApi()
        self.user_groups = None
        self.subset = subset
        super().__init__()

    def set_user_groups(self, groups):
        self.user_groups = groups

    def retrieve_project_info(self, processes=None):
        if self.subset:
            subset_path = check_list_subset_input_file_path()
            self.log.info(
                f"Listing subset of {self.config.source_host} projects from '{subset_path}'")
            self.multi.start_multi_process_stream_with_args(
                self.handle_projects_subset, get_subset_list(), processes=processes, nestable=True)
        else:
            self.multi.start_multi_process_stream_with_args(
                self.handle_retrieving_projects, self.projects_api.get_all_projects(), processes=processes, nestable=True)

    def handle_projects_subset(self, project, project_key=None):
        # e.g. https://www.bitbucketserverexample.com/projects/TEST"
        project_key = project_key or project.split("/")[4]
        try:
            project_json = self.projects_api.get_project(project_key)
            self.handle_retrieving_projects(project_json)
        except RequestException as re:
            self.log.error(
                f"Failed to GET project '{project_key}', with error:\n{re}")

    def handle_retrieving_projects(self, project, mongo=None):
        error, resp = is_error_message_present(project)
        if resp and not error:
            # mongo should be set to None unless this function is being used in a
            # unit test
            if not mongo:
                mongo = self.connect_to_mongo()
            mongo.insert_data(
                f"groups-{strip_netloc(self.config.source_host)}",
                self.format_project(resp, mongo))
            mongo.close_connection()
        else:
            self.log.error(resp)

    def format_project(self, project, mongo):
        return {
            "name": project["name"],
            "id": project["id"],
            "path": project["key"],
            "full_path": project["key"],
            "visibility": "public" if project["public"] else "private",
            "description": project.get("description", ""),
            "members": self.add_project_users([], project["key"], self.user_groups),
            "projects": self.add_project_repos([], project["key"], mongo)
        }

    def add_project_users(self, users, project_key, groups):
        bitbucket_permission_map = {
            "PROJECT_ADMIN": 50,  # Owner
            "PROJECT_WRITE": 30,  # Developer
            "PROJECT_READ": 20  # Reporter
        }
        for user in self.projects_api.get_all_project_users(project_key):
            m = user["user"]
            m["permission"] = bitbucket_permission_map[user["permission"]]
            users.append(m)

        if groups:
            for group in self.projects_api.get_all_project_groups(project_key):
                group_name = dig(group, 'group', 'name', default="").lower()
                permission = bitbucket_permission_map[group["permission"]]
                if groups.get(group_name):
                    for user in groups[group_name]:
                        temp_user = user
                        temp_user["permission"] = permission
                        users.append(temp_user)
                else:
                    self.log.warning(
                        f"Unable to find project {project_key} user group {group_name} or the group is empty")

        return remove_dupes_but_take_higher_access(
            self.users.format_users(users))

    def add_project_repos(self, repos, project_key, mongo):
        try:
            for repo in self.projects_api.get_all_project_repos(project_key):
                # Save all project repos ID references as part of group metadata
                repos.append(repo.get("id"))
                # List BB Server project repos
                if self.subset:
                    mongo.insert_data(
                        f"projects-{strip_netloc(self.config.source_host)}",
                        self.repos.format_repo(repo))
            # Remove duplicate entries
            return list(set(repos))
        except RequestException as re:
            self.log.error(
                f"Failed to GET repos from project '{project_key}', with error:\n{re}")
            return None
