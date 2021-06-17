from congregate.helpers.base_class import BaseClass
from congregate.helpers.list_utils import remove_dupes
from congregate.helpers.misc_utils import remove_dupes_but_take_higher_access
from congregate.helpers.dict_utils import dig
from congregate.helpers.json_utils import write_json_to_file
from congregate.migration.bitbucket.api.projects import ProjectsApi
from congregate.migration.bitbucket.users import UsersClient
from congregate.migration.bitbucket.repos import ReposClient
from congregate.migration.bitbucket.api.groups import GroupsApi


class ProjectsClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.users = UsersClient()
        self.repos = ReposClient()
        self.groups_api = GroupsApi()
        super().__init__()

    def retrieve_project_info(self, groups=None):
        obj = []
        projects = self.projects_api.get_all_projects()
        for project in projects:
            obj.append({
                "name": project["name"],
                "id": project["id"],
                "path": project["key"],
                "full_path": project["key"],
                "visibility": "public" if project["public"] else "private",
                "description": project.get("description", ""),
                "members": self.add_project_users([], project["key"], groups),
                "projects": self.add_project_repos([], project["key"]),
            })
        write_json_to_file(
            f"{self.app_path}/data/groups.json", remove_dupes(obj), self.log)
        return remove_dupes(obj)

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
                if groups.get(group_name, None):
                    for user in groups[group_name]:
                        temp_user = user
                        temp_user["permission"] = permission
                        users.append(temp_user)
                else:
                    self.log.warning(f"Unable to find group {group_name}")

        return remove_dupes_but_take_higher_access(self.users.format_users(users))

    def add_project_repos(self, repos, project_key):
        repos = []
        for repo in self.projects_api.get_all_project_repos(project_key):
            repos.append(self.repos.format_repo(repo, project=True))
        return remove_dupes(repos)
