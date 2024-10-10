import re
import os
from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import strip_netloc
from gitlab_ps_utils.dict_utils import dig

from congregate.helpers.base_class import BaseClass
from congregate.migration.ado.api.repositories import RepositoriesApi


class AzureDevOpsWrapper(BaseClass):

    def __init__(self, subset=False):
        self.subset = subset
        self.repositories_api = RepositoriesApi()
        self.skip_group_members = False
        self.skip_project_members = False
        super().__init__()

    def slugify(self, text):
        return re.sub(r'\s+', '-', re.sub(r'[^\w\s-]', '', text.lower())).strip('-')
    
    def format_project(self, project, repository, count, mongo):
        path_with_namespace = self.slugify(project["name"])
        if count > 1:
            path_with_namespace = os.path.join(self.slugify(project["name"]), self.slugify(repository["name"]))

        return {
            "name": repository["name"],
            "id": repository["id"],
            "path": self.slugify(repository["name"]),
            "path_with_namespace": path_with_namespace,
            "visibility": project["visibility"],
            "description": project.get("description", ""),
            "members": [],
            "http_url_to_repo": repository["remoteUrl"],
            "ssh_url_to_repo": repository["sshUrl"],
            "namespace": {
                "id": dig(repository, 'project', 'id'),
                "path": self.slugify(project["name"]),
                "name": dig(repository, 'project', 'name'),
                "kind": "group",
                "full_path": path_with_namespace
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
            "members": [],
            "projects": [] if self.subset else self.add_project_repos([], project, mongo)
        }

    def add_project_repos(self, repos, project, mongo):
        try:
            for repo in self.repositories_api.get_all_repositories(project["id"]):
                # Save all project repos ID references as part of group metadata
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
            "username": user["principalName"],
            "name": user["displayName"],
            "email": user["mailAddress"].lower()
        }
