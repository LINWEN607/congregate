from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.processes import start_multi_process_stream
from congregate.helpers.misc_utils import safe_json_response, is_error_message_present
from congregate.migration.github.api.repos import ReposApi
from congregate.migration.github.users import UsersClient
from congregate.migration.github.api.users import UsersApi
from congregate.migration.gitlab.api.projects import ProjectsApi


class ReposClient(BaseClass):
    REPO_PERMISSIONS_MAP = {
        ((u"admin", True), (u"push", True), (u"pull", True)): 40,  # Maintainer
        ((u"admin", False), (u"push", True), (u"pull", True)): 30,  # Developer
        ((u"admin", False), (u"push", False), (u"pull", True)): 20  # Reporter
    }

    GROUP_TYPE = ["Organization", "Enterprise"]

    def __init__(self, host, token):
        super(ReposClient, self).__init__()
        self.repos_api = ReposApi(host, token)
        self.users = UsersClient(host, token)
        self.users_api = UsersApi(host, token)
        self.gl_project_api = ProjectsApi()

    def retrieve_repo_info(self, processes=None):
        """
        List and transform all GitHub public repo to GitLab project metadata
        """
        start_multi_process_stream(
            self.handle_retrieving_repos, self.repos_api.get_all_public_repos(), processes=processes)

    def connect_to_mongo(self):
        return MongoConnector()

    def handle_retrieving_repos(self, repo, mongo=None):
        if not mongo:
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
            "members": self.add_repo_members(repo["owner"]["type"], repo["owner"]["login"], repo["name"], mongo) if not org else []
        }

    def add_repo_members(self, kind, owner, repo, mongo):
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
        return self.users.format_users(members, mongo)

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

    def migrate_gh_project_protected_branch(self, new_id, repo):
        is_result = False
        branches = self.repos_api.get_list_branches(
            repo["namespace"], repo["path"])
        for branch in branches:
            if branch["protected"]:
                single_branch = self.format_protected_branch(
                    new_id, branch["name"])
                r = self.gl_project_api.protect_repository_branches(
                    new_id, branch["name"], self.config.destination_host, self.config.destination_token, single_branch)
                if r.status_code != 201:
                    # Unprotect the protected branch
                    self.gl_project_api.unprotect_repository_branches(
                        new_id, branch["name"], self.config.destination_host, self.config.destination_token)
                    # Added protected branch
                    self.gl_project_api.protect_repository_branches(
                        new_id, branch["name"], self.config.destination_host, self.config.destination_token, single_branch)
                is_result = True
        return is_result

    def format_protected_branch(self, repo_id, branch_name):
        return {
            "id": repo_id,
            "name": branch_name,
            "allowed_to_push": [{"access_level": 0}],
            "code_owner_approval_required": False
        }

    def migrate_gh_project_level_mr_approvals(self, new_id, repo):
        is_result = False
        conf = {}
        default_branch = safe_json_response(self.repos_api.get_single_project_protected_branch(
            repo["namespace"], repo["path"], "master"))
        if default_branch is not None:
            # migrate configuration
            conf = self.format_project_level_configuration(
                new_id, default_branch)
        else:
            return False
        if is_error_message_present(conf) or not conf:
            self.log.error(
                "Failed to fetch GitHub Pull request approval configuration ({0}) for project {1}".format(conf, repo["name"]))
            return False
        else:
            self.log.info(
                "Migrating project-level MR approval configuration for {0} (New ID: {1}) to GitLab".format(repo["name"], new_id))
            self.gl_project_api.change_project_level_mr_approval_configuration(
                new_id, self.config.destination_host, self.config.destination_token, conf)
        # migrate approval rules
        protected_branch_ids = []
        gl_projected_branches = self.gl_project_api.get_all_project_protected_branches(
            new_id, self.config.destination_host, self.config.destination_token)
        for branch in gl_projected_branches:
            protected_branch_ids.append(branch["id"])

        rule = self.format_project_level_mr_rule(new_id, protected_branch_ids)
        if is_error_message_present(rule) or not rule:
            self.log.error(
                "Failed to generate MR approval rules ({0}) for project {1}".format(rule, repo["name"]))
            return False
        else:
            self.gl_project_api.create_project_level_mr_approval_rule(
                new_id, self.config.destination_host, self.config.destination_token, rule)
            return True

    def format_project_level_configuration(self, new_id, branch):
        return {
            "id": new_id,
            "approvals_before_merge": 1,
            "reset_approvals_on_push": True if branch.get("required_pull_request_reviews", None) and branch["required_pull_request_reviews"]["dismissal_restrictions"]["users"] else False,
            "disable_overriding_approvers_per_merge_request": False,
            "merge_requests_author_approval": False,
            "merge_requests_disable_committers_approval": False,
            "require_password_to_approve": False
        }

    def format_project_level_mr_rule(self, new_id, protected_branch_ids, user_ids=None, group_ids=None):
        return{
            "id": new_id,
            "name": "gh_pr_rules",
            "rule_type": "regular",
            "user_ids": user_ids,
            "group_ids": group_ids,
            "approvals_required": 1,
            "protected_branch_ids": protected_branch_ids
        }

    def migrate_archived_repo(self, new_id, repo):
        gh_repo = safe_json_response(
            self.repos_api.get_repo(repo["namespace"], repo["path"]))
        if gh_repo and gh_repo.get("archived", None):
            self.gl_project_api.archive_project(
                self.config.destination_host, self.config.destination_token, new_id)
            return True
        return False
