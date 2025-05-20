import botocore
import re
import os
from gitlab_ps_utils.misc_utils import strip_netloc

from congregate.helpers.base_class import BaseClass
from congregate.migration.codecommit.api.base import CodeCommitApiWrapper


class CodeCommitWrapper(BaseClass):

    def __init__(self, subset=False):
        self.subset = subset
        self.repositories_api = CodeCommitApiWrapper()
        self.skip_group_members = True
        self.skip_project_members = True
        self.project = "CodeCommit"
        super().__init__()

   

    def slugify(self, text):
        return re.sub(r'\s+', '-', re.sub(r'[^\w\s-]', '', text.lower())).strip('-')

    def format_project(self, project, repository, count, mongo):
        path_with_namespace = self.slugify(project)
        if count > 1:
            path_with_namespace = os.path.join(self.slugify(project), self.slugify(repository["repositoryMetadata"]["repositoryName"]))
        return {
            "name": repository["repositoryMetadata"]["repositoryName"],
            "id": repository["repositoryMetadata"]["repositoryId"],
            "path": self.slugify(repository["repositoryMetadata"]["repositoryName"]),
            "path_with_namespace": path_with_namespace,
            "visibility": "private",
            "description": "",
            "members": [],
            "http_url_to_repo": repository["repositoryMetadata"]["cloneUrlHttp"],
            "ssh_url_to_repo": repository["repositoryMetadata"]["cloneUrlSsh"],
            "default_branch": repository["repositoryMetadata"]["defaultBranch"],
            "namespace": {
                "id": repository["repositoryMetadata"]["accountId"],
                "path": self.slugify(project),
                "name": project,
                "kind": "group",
                "full_path": project
            },
        }
        
    def format_group(self, project, repository, mongo):
        return {
            "name": project,
            "id": repository[0]["repositoryMetadata"]["repositoryId"],
            "path": self.slugify(project),
            "full_path": self.slugify(project),
            "visibility": "private",
            "description": "",
            "members": [] ,
            "projects": []
        }