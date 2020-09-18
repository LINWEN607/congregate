import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes, safe_json_response, is_error_message_present, read_json_file_into_object
from congregate.migration.github.api.repos import ReposApi
from congregate.migration.github.users import UsersClient
from congregate.migration.github.api.users import UsersApi


class ReposClient(BaseClass):
    REPO_PERMISSIONS_MAP = {
        ((u"admin", True), (u"push", True), (u"pull", True)): 40,  # Maintainer
        ((u"admin", False), (u"push", True), (u"pull", True)): 30,  # Developer
        ((u"admin", False), (u"push", False), (u"pull", True)): 20  # Reporter
    }

    GROUP_TYPE = ["Organization", "Enterprise"]

    def __init__(self):
        super(ReposClient, self).__init__()
        self.repos_api = ReposApi(
                                  self.config.source_host, 
                                  self.config.source_token)
        self.users = UsersClient()
        self.users_api = UsersApi(
                                  self.config.source_host, 
                                  self.config.source_token) 
        
    def retrieve_repo_info(self):
        """
        List and transform all GitHub public repo to GitLab project metadata
        """
        projects = []
        self.format_repos(projects, self.repos_api.get_all_public_repos())
        with open('%s/data/project_json.json' % self.app_path, "w") as f:
            json.dump(remove_dupes(projects), f, indent=4)
        return remove_dupes(projects)

    def format_repos(self, projects, listed_repos, org=False):
        """
        Format public and org/team repos.
        Leave org/team repo members empty ([]) as they are retrieved during staging.
        """
        if projects is None:
            self.log.error("Failed to format repos {}".format(projects))
        else:
            for repo in listed_repos:
                projects.append({
                    "id": repo["id"],
                    "path": repo["name"],
                    "name": repo["name"],
                    "ci_sources": {
                        "Jenkins": self.list_ci_sources_jenkins(repo["name"]),
                        "TeamCity": self.list_ci_sources_teamcity(repo["name"])
                    },
                    "namespace": {
                        "id": repo["owner"]["id"],
                        "path": repo["owner"]["login"],
                        "name": repo["owner"]["login"],
                        "kind": "group" if repo["owner"]["type"] in self.GROUP_TYPE else "user",
                        "full_path": repo["owner"]["login"]
                    },
                    "http_url_to_repo": repo["html_url"] + ".git",
                    "path_with_namespace": repo["full_name"],
                    "visibility": "private" if repo["private"] else "public",
                    "description": repo.get("description", ""),
                    "members": self.add_repo_members(repo["owner"]["type"], repo["owner"]["login"], repo["name"]) if not org else []
                })
        return projects

    def add_repo_members(self, kind, owner, repo):
        """
        User repos have a single owner and collaborators (requires a collaborator PAT).
        Org and team repos have collaborators (may require a collaborator PAT).
        """
        if kind in self.GROUP_TYPE:
            members = []
            # TODO: Determine single PAT for retrieving repo/org/team collaborators
            # for c in self.repos_api.get_all_repo_collaborators(owner, repo):
            #     c["permissions"] = self.REPO_PERMISSIONS_MAP[tuple(
            #         c.get("permissions", None).items())]
            #     members.append(c)
        elif kind == "User":
            members = [{"login": owner}]
            user_repo = safe_json_response(
                self.repos_api.get_repo(owner, repo))
            if not user_repo or is_error_message_present(user_repo):
                self.log.error("Failed to get JSON for user {} repo {} ({})".format(
                    owner, repo, user_repo))
                return []
            else:
                members[0]["permissions"] = self.REPO_PERMISSIONS_MAP[tuple(user_repo.get(
                    "permissions", None).items())]
        return self.users.format_users(members)
    
    def list_ci_sources_jenkins(self, repo_name):
        list_job_names = []

        if self.config.ci_source_type == "jenkins":
            ci_sources_jobs = read_json_file_into_object(f"{self.app_path}/data/jenkins_jobs.json")
            for job in ci_sources_jobs:
                if job["url"] is not None:
                    temp_list = job["url"].split("/")
                    if repo_name == temp_list[-1][:-4]:
                        list_job_names.append(job["name"])

        return list_job_names
     
    def list_ci_sources_teamcity(self, repo_name):
        list_job_names = []

        if self.config.ci_source_type == "teamcity":
            ci_sources_jobs = read_json_file_into_object(f"{self.app_path}/data/teamcity_jobs.json")
            for job in ci_sources_jobs:
                if job["url"] is not None:
                    temp_list = job["url"].split("/")
                    if repo_name == temp_list[-1][:-4]:
                        list_job_names.append(job["name"])

        return list_job_names