import re
import os
from unidecode import unidecode 
from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import strip_netloc
from gitlab_ps_utils.dict_utils import dig

from congregate.helpers.base_class import BaseClass
from congregate.migration.ado.api.repositories import RepositoriesApi
from congregate.migration.ado.api.users import UsersApi
from congregate.migration.ado.api.teams import TeamsApi


class AzureDevOpsWrapper(BaseClass):

    def __init__(self, subset=False):
        self.subset = subset
        self.repositories_api = RepositoriesApi()
        self.users_api = UsersApi()
        self.teams_api = TeamsApi()
        self.skip_group_members = False
        self.skip_project_members = False
        super().__init__()

    def slugify(self, text):
        return re.sub(r'\s+', '-', re.sub(r'[^\w\s-]', '', text.lower())).strip('-')

    def create_valid_username(self, input_string):
        transliterated_string = unidecode(input_string)
        lowercase_string = transliterated_string.lower()
        dotted_string = lowercase_string.replace(' ', '.')
        valid_username = re.sub(r'[^a-z.]', '', dotted_string)
        valid_username = valid_username.strip('.')
        valid_username = re.sub(r'\.+', '.', valid_username)
        return valid_username

    def create_valid_name(self, input_string):
        transliterated_string = unidecode(input_string)
        return transliterated_string

    def format_project(self, project, repository, count, mongo):
        path_with_namespace = self.slugify(project["name"])
        if count > 1:
            path_with_namespace = os.path.join(self.slugify(project["name"]), self.slugify(repository["name"]))

        if len(path_with_namespace.split("/")) > 1:
            full_path = path_with_namespace.split("/")[0]   
        else: 
            full_path = path_with_namespace
            
        return {
            "name": repository["name"],
            "id": repository["id"],
            "path": self.slugify(repository["name"]),
            "path_with_namespace": path_with_namespace,
            "visibility": project["visibility"],
            "description": project.get("description", ""),
            "members": [] if self.subset else self.add_team_members([], project),
            "http_url_to_repo": repository["remoteUrl"],
            "ssh_url_to_repo": repository["sshUrl"],
            "namespace": {
                "id": dig(repository, 'project', 'id'),
                "path": self.slugify(project["name"]),
                "name": dig(repository, 'project', 'name'),
                "kind": "group",
                "full_path": full_path
            },
        }

    def format_group(self, project, mongo):
        return {
            "name": project["name"],
            "id": project["id"],
            "path": self.slugify(project["name"]),
            "full_path": self.slugify(project["name"]),
            "visibility": project["visibility"],
            "description": project.get("description", ""),
            "members": [] if self.subset else self.add_team_members([], project),
            "projects": [] if self.subset else self.add_project_repos([], project, mongo)
        }

    def add_project_repos(self, repos, project, mongo):
        try:
            for repo in self.repositories_api.get_all_repositories(project["id"]):
                # Save all project repos ID references as part of group metadata
                if repo.get("isDisabled") is False and repo.get("size") > 0:
                    repos.append(repo.get("id"))
                    if mongo is not None:
                        mongo.insert_data(
                            f"projects-{strip_netloc(self.config.source_host)}",
                            self.format_project(project, repo, len(repos), mongo))
            # Remove duplicate entries
            return list(set(repos))
        except RequestException as re:
            self.log.error(
                f"Failed to GET repos from project '{project}', with error:\n{re}")
            return None

    def format_user(self, user):
        return {
            "id": user["descriptor"],
            "username": self.create_valid_username(user.get("displayName")),
            "name": self.create_valid_name(user.get("displayName")),
            "email": user["mailAddress"].lower(),
            "state": "active"
        }

    def add_team_members(self, users, project):
        users = []
        for team in self.teams_api.get_teams(project["id"]):
            for member in self.teams_api.get_team_members(project["id"], team["id"]):
                if member["identity"].get("isContainer"):
                    for group_member in self.users_api.get_group_members(member["identity"].get('id')):
                        user_descriptor = group_member["user"]["descriptor"]
                        user_data = self.users_api.get_user(user_descriptor)
                        if user_data:
                            users.append(self.format_user(user_data.json()))
                else:
                    user_descriptor = member["identity"]["descriptor"]
                    user_data = self.users_api.get_user(user_descriptor)
                    if user_data:
                        users.append(self.format_user(user_data.json()))
        users = [dict(t) for t in {tuple(d.items()) for d in users}]
        return users
