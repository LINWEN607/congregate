from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.processes import start_multi_process_stream
from congregate.helpers.misc_utils import safe_json_response, is_error_message_present, read_json_file_into_object
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
        
    def retrieve_repo_info(self, processes=None):
        """
        List and transform all GitHub public repo to GitLab project metadata
        """
        start_multi_process_stream(self.handle_retrieving_repos, self.repos_api.get_all_public_repos(), processes=processes)

    def connect_to_mongo(self):
        return MongoConnector()
    
    def handle_retrieving_repos(self, repo):
        mongo = self.connect_to_mongo()
        data = self.format_repo(repo, mongo)
        mongo.insert_data("projects", data)
        mongo.close_connection()

    def format_repo(self, repo, mongo, org=False):
        """
        Format public and org/team repos.
        Leave org/team repo members empty ([]) as they are retrieved during staging.
        """
        repo_url = repo["html_url"] + ".git"
        return {
                "id": repo["id"],
                "path": repo["name"],
                "name": repo["name"],
                "ci_sources": {
                    "Jenkins": self.list_ci_sources_jenkins(repo_url, mongo),
                    "TeamCity": self.list_ci_sources_teamcity(repo_url, mongo)
                },
                "namespace": {
                    "id": repo["owner"]["id"],
                    "path": repo["owner"]["login"],
                    "name": repo["owner"]["login"],
                    "kind": "group" if repo["owner"]["type"] in self.GROUP_TYPE else "user",
                    "full_path": repo["owner"]["login"]
                },
                "http_url_to_repo": repo_url,
                "path_with_namespace": repo["full_name"],
                "visibility": "private" if repo["private"] else "public",
                "description": repo.get("description", ""),
                "members": self.add_repo_members(repo["owner"]["type"], repo["owner"]["login"], repo["name"]) if not org else []
            }

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
    
    def list_ci_sources_jenkins(self, repo_url, mongo):
        data = []
        for c in mongo.wildcard_collection_query("jenkins"):
            for r in mongo.db[c].find({"url": repo_url}):
                data.append(r["name"])
        return data

    def list_ci_sources_teamcity(self, repo_url, mongo):
        data = []
        for c in mongo.wildcard_collection_query("teamcity"):
            for r in mongo.db[c].find({"url": repo_url}):
                data.append(r["name"])
        return data
     