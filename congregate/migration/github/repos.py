from time import time
from requests.exceptions import RequestException
from gitlab_ps_utils.misc_utils import get_dry_log, is_error_message_present, safe_json_response, strip_netloc
from gitlab_ps_utils.json_utils import json_pretty
from gitlab_ps_utils.dict_utils import dig

from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector
from congregate.migration.github.api.repos import ReposApi
from congregate.migration.github.users import UsersClient
from congregate.migration.github.api.users import UsersApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.helpers.migrate_utils import get_staged_projects, add_post_migration_stats
from congregate.helpers.utils import is_github_dot_com, rotate_logs


class ReposClient(BaseClass):
    # GitHub source - https://docs.github.com/en/organizations/managing-access-to-your-organizations-repositories/repository-roles-for-an-organization
    REPO_PERMISSIONS_MAP = {
        # Maintainer
        ((u"admin", True), (u"maintain", True), (u"push", True), (u"triage", True), (u"pull", True)): 40,
        ((u"admin", True), (u"push", True), (u"pull", True)): 40,
        # Developer
        ((u"admin", False), (u"maintain", False), (u"push", True), (u"triage", True), (u"pull", True)): 30,
        ((u"admin", False), (u"push", True), (u"pull", True)): 30,
        # Reporter
        ((u"admin", False), (u"maintain", False), (u"push", False), (u"triage", True), (u"pull", True)): 20,
        ((u"admin", False), (u"push", False), (u"pull", True)): 20
    }

    REPO_PERMISSIONS_MAP_V4 = {
        "ADMIN": 40,      # Equivalent to having admin rights
        "MAINTAIN": 40,   # Equivalent to being a maintainer
        "WRITE": 30,      # Equivalent to having push rights
        "TRIAGE": 20,     # Equivalent to having triage rights
        "READ": 20        # Equivalent to having read rights
    }

    GROUP_TYPE = ["Organization", "Enterprise"]

    def __init__(self, host, token, processes=None):
        super().__init__()
        self.repos_api = ReposApi(host, token)
        self.users = UsersClient(host, token)
        self.users_api = UsersApi(host, token)
        self.gl_projects_api = ProjectsApi()
        self.gl_projects = ProjectsClient()
        self.host = strip_netloc(host)
        self.processes = processes
        self.sub_processes = self.split_processes(processes)

    def split_processes(self, processes):
        """
            Splits number of sub processes to subset of set number of processes

            Max number of sub processes is 8. This function is a bit of a balancing act of performance and stability
        """
        if processes and processes > 8 and processes < 16:
            return processes / 2
        return 4

    def retrieve_repo_info(self, processes=None):
        """
        List and transform all GitHub public repo to GitLab project metadata
        """
        if is_github_dot_com(
                self.config.source_host) or self.config.src_parent_org:
            self.log.warning(
                f"NOT listing public repos on {self.config.source_host}")
        else:
            self.multi.start_multi_process_stream(
                self.handle_retrieving_repos, self.repos_api.get_all_public_repos(), processes=processes, nestable=True)

    def handle_retrieving_repos(self, repo, mongo=None):
        if not mongo:
            mongo = CongregateMongoConnector()
        data = self.format_repo(repo, mongo)
        mongo.insert_data(f"projects-{self.host}", data)
        mongo.close_connection()

    def format_repo(self, repo, mongo, org=False):
        """
        Format public and org/team repos.
        Leave org/team repo members empty ([]) as they are retrieved during staging.
        """
        repo_url = repo["url"] + ".git"
        repo_path = dig(repo, 'owner', 'login')
        repo_type = dig(repo, 'owner', 'type')
        repo_name = repo.get('name')
        return {
            "id": repo.get("id"),
            "path": repo_name,
            "name": repo_name,
            "ci_sources": {
                "Jenkins": self.list_ci_sources_jenkins(repo_url, mongo) if self.config.jenkins_ci_source_host else [],
                "TeamCity": self.list_ci_sources_teamcity(repo_url, mongo) if self.config.tc_ci_source_host else []},
            "namespace": {
                "id": dig(repo, 'owner', 'id'),
                "path": repo_path,
                "name": repo_path,
                "kind": "group" if repo_type in self.GROUP_TYPE else "user",
                "full_path": repo_path},
            "http_url_to_repo": repo_url,
            "path_with_namespace": repo.get("nameWithOwner"),
            "visibility": repo.get("visibility"),
            "description": repo.get("description", ""),
            # This request is extremely slow at scale and needs a refactor
            # "members": []
            "members": [] if org else self.add_repo_members(
                repo["owner"]["type"],
                repo["owner"]["login"],
                repo["name"],
                mongo)}

    def add_repo_members(self, kind, owner, repo, mongo):
        """
        User repos have a single owner and collaborators (requires a collaborator PAT).
        Org and team repos have collaborators (may require a collaborator PAT).
        """
        try:
            if kind in self.GROUP_TYPE:
                members = []
                # TODO: Determine single PAT for retrieving repo/org/team
                # collaborators
                # for c in self.repos_api.get_all_repo_collaborators(owner, repo):
                #     if c:
                #         c["permissions"] = self.REPO_PERMISSIONS_MAP[tuple(
                #             c.get("permissions").items())]
                #         members.append(c)
                #     else:
                #         break
            elif kind == "User":
                members = [{"login": owner}]
                user_repo = safe_json_response(
                    self.repos_api.get_repo_v4(owner, repo))
                error, user_repo = is_error_message_present(user_repo)
                if error or not user_repo:
                    self.log.error(
                        f"Failed to get JSON for user {owner} repo {repo}: {user_repo}")
                    return []
                members[0]["permissions"] = self.REPO_PERMISSIONS_MAP_V4.get(user_repo['data']['repository']['viewerPermission'], 0)

            return self.users.format_users(members, mongo)
        except KeyError as ke:
            self.log.error(
                f"Failed to map repo {repo} (type: {kind}) permission, with Key error:\n{ke}")
            return []

    def list_ci_sources_jenkins(self, repo_url, mongo):
        data = []
        for c in mongo.wildcard_collection_query("jenkins"):
            for r in mongo.safe_find(
                c,
                query={"url": repo_url},
                hint="url_1"
            ):
                data.append(r["name"])
        return data

    def list_ci_sources_teamcity(self, repo_url, mongo):
        data = []
        for c in mongo.wildcard_collection_query("teamcity"):
            for r in mongo.safe_find(
                c,
                query={"url": repo_url},
                hint="url_1"
            ):
                data.append(r["name"])
        return data

    def migrate_gh_project_protected_branch(self, new_id, repo):
        """
            Migrates any protected branches.
            Always returns true due to self.multi.start_multi_process_stream_with_args return value

            :param: new_id: (int) Project ID
            :param: repo: (dict) GitHub Repo metadata
            :return: True (We just assume it works. Check the logs for any errors)
        """
        self.multi.start_multi_process_stream_with_args(
            self.handle_protected_branches,
            self.repos_api.get_repo_branches_v4(
                repo["namespace"],
                repo["path"]),
            new_id,
            processes=self.sub_processes)
        return True

    def handle_protected_branches(self, new_id, branch):
        if branch["branchProtectionRule"]:
            single_branch = self.format_protected_branch(
                new_id, branch["name"])
            r = self.gl_projects_api.protect_repository_branches(
                new_id,
                branch["name"],
                self.config.destination_host,
                self.config.destination_token,
                single_branch)
            if r.status_code != 201:
                # Unprotect the protected branch
                self.gl_projects_api.unprotect_repository_branches(
                    new_id,
                    branch["name"],
                    self.config.destination_host,
                    self.config.destination_token)
                # Added protected branch
                self.gl_projects_api.protect_repository_branches(
                    new_id,
                    branch["name"],
                    self.config.destination_host,
                    self.config.destination_token,
                    single_branch)

    def format_protected_branch(self, repo_id, branch_name):
        return {
            "id": repo_id,
            "name": branch_name,
            "allowed_to_push": [{"access_level": 0}],
            "code_owner_approval_required": False
        }

    def migrate_gh_project_level_mr_approvals(self, new_id, repo):
        conf = {}
        default_branch = safe_json_response(
            self.repos_api.get_single_project_protected_branch(
                repo["namespace"], repo["path"], "master"))
        if default_branch is not None:
            # migrate configuration
            conf = self.format_project_level_configuration(
                new_id, default_branch)
        else:
            return False
        error, conf = is_error_message_present(conf)
        if error or not conf:
            self.log.error(
                "Failed to fetch GitHub Pull request approval configuration ({0}) for project {1}".format(
                    conf, repo["name"]))
            return False
        self.log.info(
            "Migrating project-level MR approval configuration for {0} (New ID: {1}) to GitLab".format(
                repo["name"], new_id))
        self.gl_projects_api.change_project_level_mr_approval_configuration(
            new_id, self.config.destination_host, self.config.destination_token, conf)

        # TODO: Refactor this method (and format_project_level_mr_rule) or remove completely
        # # migrate approval rules
        # protected_branch_ids = []
        # for branch in self.gl_projects_api.get_all_project_protected_branches(
        #         new_id, self.config.destination_host, self.config.destination_token):
        #     protected_branch_ids.append(branch["id"])

        # dest_user_ids = []
        # for user in self.get_email_list_of_reviewers_for_pr(
        #         repo["namespace"], repo["path"]):
        #     if dest_user := find_user_by_email_comparison_without_id(user):
        #         dest_user_ids.append(dest_user["id"])

        # rule = self.format_project_level_mr_rule(
        #     new_id, protected_branch_ids, dest_user_ids)

        # error, rule = is_error_message_present(rule)
        # if error or not rule:
        #     self.log.error(
        #         "Failed to generate MR approval rules ({0}) for project {1}".format(
        #             rule, repo["name"]))
        #     return False
        # else:
        #     self.gl_projects_api.create_project_level_mr_approval_rule(
        #         new_id, self.config.destination_host, self.config.destination_token, rule)
        #     return True

    def format_project_level_configuration(self, new_id, branch):
        return {
            "id": new_id,
            "approvals_before_merge": 1,
            "reset_approvals_on_push": branch.get("required_pull_request_reviews") and dig(branch, 'required_pull_request_reviews', 'dismissal_restrictions', 'users'),
            "disable_overriding_approvers_per_merge_request": False,
            "merge_requests_author_approval": False,
            "merge_requests_disable_committers_approval": False,
            "require_password_to_approve": False}

    # def format_project_level_mr_rule(self, protected_branch_ids, user_ids=None, group_ids=None):
    #     return{
    #         "name": "gh_pr_rules",
    #         "rule_type": "regular",
    #         "user_ids": user_ids,
    #         "group_ids": group_ids,
    #         "approvals_required": 1,
    #         "protected_branch_ids": protected_branch_ids
    #     }

    def transform_gh_repo_commit(self, commits):
        return [{
            "id": c["sha"],
            "message": c["message"],
            "author_name": dig(c, 'commit', 'author', 'name'),
            "author_email": dig(c, 'commit', 'author', 'email'),
            "authored_date": dig(c, 'commit', 'author', 'date'),
            "committer_name": dig(c, 'commit', 'committer', 'name'),
            "committer_email": dig(c, 'commit', 'committer', 'email'),
            "committed_date": dig(c, 'commit', 'committer', 'date'),
        } for c in commits]

    def transform_gh_branches(self, branches):
        return [{
            "name": b["name"],
                    "commit": {
                        "id": b['target']['oid'],
            },
            "protected": b["branchProtectionRule"],
        } for b in branches]

    def transform_gh_pull_requests(self, pull_requests):
        return [{
            "title": pr["title"],
            "description": pr["body"],
            "state": "opened" if pr["state"] == "open" else "closed",
            "created_at": pr["created_at"],
            "updated_at": pr["updated_at"],
            "author": {
                "username": dig(pr, 'author', 'login'),
            },
            "assignees": [{
                "username": a["login"]
            } for a in pr['assignees']['nodes']],
            "work_in_progress": pr["draft"],
            "milestone": pr["milestone"]["title"]
        } for pr in pull_requests]

    def transform_gh_tags(self, tags):
        return [{
            "name": t["name"],
            "commit": {
                "id": dig(t, 'target', 'oid'),
            }
        } for t in tags]

    def transform_gh_milestones(self, milestones):
        return [{
            "title": m["title"],
            "description": m["description"],
            "state": "active" if m["state"] == "open" else "closed",
            "created_at": m["created_at"],
            "updated_at": m["updated_at"],
            "due_date": m["due_on"],
        } for m in milestones]

    def transform_gh_releases(self, releases):
        return [{
            "name": r["name"],
            "tag_name": r["tag_name"],
            "description": r["body"],
            "created_at": r["created_at"],
            "released_at": r["published_at"],
            "author": {
                "username": dig(r, 'author', 'login'),
            },
            "upcoming_release": r["prerelease"],
        } for r in releases]

    def transform_gh_pr_comments(self, pr_comments):
        return [{
            "body": c["body"],
            "author": {
                "username": dig(c, 'user', 'login'),
            },
            "created_at": c["created_at"],
            "updated_at": c["updated_at"],
        } for c in pr_comments]

    def transform_gh_issues(self, issues):
        return [{
            "title": i["title"],
            "description": i["body"],
            "state": i.get("state", "closed"),
            "created_at": i["created_at"],
            "updated_at": i["updated_at"],
            "closed_at": i["closed_at"],
            "labels": [l["name"] for l in i.get("labels", [])],
            "milestone": i["milestone"],
            "assignees": [a["login"] for a in i.get("assignees", [])],
            "author": {
                "username": dig(i, 'user', 'login'),
            },
            "assignee": i["assignee"],
            "user_notes_count": i["comments"],
            "discussion_locked": i["locked"],
        } for i in issues]

    def archive_migrated_repo(self, new_id, repo):
        gh_repo = safe_json_response(
            self.repos_api.get_repo(repo["namespace"], repo["path"]))
        if gh_repo and gh_repo.get("archived"):
            self.gl_projects_api.archive_project(
                self.config.destination_host, self.config.destination_token, new_id)
            return True
        return False

    def update_staged_repos_archive_state(self, archived=True, dry_run=True):
        start = time()
        rotate_logs()
        staged_projects = get_staged_projects()
        self.log.info(f"GitHub repo count: {len(staged_projects)}")
        try:
            for sp in staged_projects:
                self.log.info(
                    f"{get_dry_log(dry_run)}{'Archiving' if archived else 'Unarchiving'} GitHub repo '{sp['path_with_namespace']}'")
                if not dry_run:

                    self.repos_api.update_repo(
                        sp["namespace"], sp["name"], {"archived": archived})
        except RequestException as re:
            self.log.error(
                f"Failed to {'' if archived else 'un'}archive staged repo, with error:\n{re}")
        finally:
            add_post_migration_stats(start, log=self.log)

    def get_email_list_of_reviewers_for_pr(self, owner, repo):
        user_emails_dict = {}
        self.multi.start_multi_process_stream_with_args(
            self.handle_list_of_reviewers,
            self.repos_api.get_repo_pulls_v4(
                owner,
                repo),
            owner,
            repo,
            user_emails_dict,
            processes=self.sub_processes)
        self.log.info(
            f"PR reviewers found: \n {json_pretty(user_emails_dict)}")
        return user_emails_dict.values()

    def handle_list_of_reviewers(self, owner, repo, user_emails_dict, pull):
        mongo = CongregateMongoConnector()
        if reviewers := safe_json_response(
            self.repos_api.list_reviewers_for_a_pull_request(
                owner, repo, pull["number"])):
            for user in reviewers.get("users", []):
                if not user_emails_dict.get(user['login']):
                    single_user = safe_json_response(
                        self.users_api.get_user(user["login"]))
                    if email := self.users.get_email_address(
                            single_user, None, mongo):
                        user_emails_dict[user['login']] = email
        mongo.close_connection()
