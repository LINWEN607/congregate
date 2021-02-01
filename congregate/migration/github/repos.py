from time import time
from requests.exceptions import RequestException
from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.processes import start_multi_process_stream, start_multi_process_stream_with_args
from congregate.migration.github.api.repos import ReposApi
from congregate.migration.github.users import UsersClient
from congregate.migration.github.api.users import UsersApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.users import UsersClient as GitLabUsersClient
from congregate.helpers.misc_utils import get_dry_log, is_error_message_present, safe_json_response, \
    add_post_migration_stats, rotate_logs, is_github_dot_com, json_pretty



class ReposClient(BaseClass):
    REPO_PERMISSIONS_MAP = {
        ((u"admin", True), (u"push", True), (u"pull", True)): 40,  # Maintainer
        ((u"admin", False), (u"push", True), (u"pull", True)): 30,  # Developer
        ((u"admin", False), (u"push", False), (u"pull", True)): 20  # Reporter
    }

    GROUP_TYPE = ["Organization", "Enterprise"]

    def __init__(self, host, token, processes=None):
        super(ReposClient, self).__init__()
        self.repos_api = ReposApi(host, token)
        self.users = UsersClient(host, token)
        self.users_api = UsersApi(host, token)
        self.gl_projects_api = ProjectsApi()
        self.gl_projects = ProjectsClient()
        self.gl_users = GitLabUsersClient()
        self.host = host.split("//")[-1]
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
        if is_github_dot_com(self.config.source_host) or self.config.src_parent_org:
            self.log.warning(
                f"NOT listing public repos on {self.config.source_host}")
        else:
            start_multi_process_stream(
                self.handle_retrieving_repos, self.repos_api.get_all_public_repos(), processes=processes)

    def connect_to_mongo(self):
        return MongoConnector()

    def handle_retrieving_repos(self, repo, mongo=None):
        if not mongo:
            mongo = self.connect_to_mongo()
        data = self.format_repo(repo, mongo)
        mongo.insert_data(f"projects-{self.host}", data)
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
                "Jenkins": self.list_ci_sources_jenkins(
                    repo_url,
                    mongo),
                "TeamCity": self.list_ci_sources_teamcity(
                    repo_url,
                    mongo)},
            "namespace": {
                "id": repo["owner"]["id"],
                "path": repo["owner"]["login"],
                "name": repo["owner"]["login"],
                "kind": "group" if repo["owner"]["type"] in self.GROUP_TYPE else "user",
                "full_path": repo["owner"]["login"]},
            "http_url_to_repo": repo_url,
            "path_with_namespace": repo["full_name"],
            "visibility": "private" if repo["private"] else "public",
            "description": repo.get(
                "description",
                ""),
            # Temporarily commenting this out. This request is extremely 
            # slow at scale and needs a refactor
            #
            # "members": self.add_repo_members(
            #     repo["owner"]["type"],
            #     repo["owner"]["login"],
            #     repo["name"],
            #     mongo) if not org else []
            "members": []
            }

    def add_repo_members(self, kind, owner, repo, mongo):
        """
        User repos have a single owner and collaborators (requires a collaborator PAT).
        Org and team repos have collaborators (may require a collaborator PAT).
        """
        if kind in self.GROUP_TYPE:
            members = []
            # TODO: Determine single PAT for retrieving repo/org/team
            # collaborators
            for c in self.repos_api.get_all_repo_collaborators(owner, repo):
                if c:
                    c["permissions"] = self.REPO_PERMISSIONS_MAP[tuple(
                        c.get("permissions", None).items())]
                    members.append(c)
                else:
                    break
        elif kind == "User":
            members = [{"login": owner}]
            user_repo = safe_json_response(
                self.repos_api.get_repo(owner, repo))
            if not user_repo or is_error_message_present(user_repo):
                self.log.error(
                    "Failed to get JSON for user {} repo {} ({})".format(
                        owner, repo, user_repo))
                return []
            else:
                members[0]["permissions"] = self.REPO_PERMISSIONS_MAP[tuple(
                    user_repo.get("permissions", None).items())]
        return self.users.format_users(members, mongo)

    def list_ci_sources_jenkins(self, repo_url, mongo):
        data = []
        for c in mongo.wildcard_collection_query("jenkins"):
            for r in mongo.safe_find(c, query={"url": repo_url}, hint="url_1"):
                data.append(r["name"])
        return data

    def list_ci_sources_teamcity(self, repo_url, mongo):
        data = []
        for c in mongo.wildcard_collection_query("teamcity"):
            for r in mongo.safe_find(c, query={"url": repo_url}, hint="url_1"):
                data.append(r["name"])
        return data

    def migrate_gh_project_protected_branch(self, new_id, repo):
        """
            Migrates any protected branches.
            Always returns true due to start_multi_process_stream_with_args return value

            :param: new_id: (int) Project ID
            :param: repo: (dict) GitHub Repo metadata
            :return: True (We just assume it works. Check the logs for any errors)
        """
        start_multi_process_stream_with_args(
            self.handle_protected_branches,
            self.repos_api.get_repo_branches(
                repo["namespace"],
                repo["path"]),
            new_id,
            processes=self.sub_processes)
        return True

    def handle_protected_branches(self, new_id, branch):
        if branch["protected"]:
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
        if is_error_message_present(conf) or not conf:
            self.log.error(
                "Failed to fetch GitHub Pull request approval configuration ({0}) for project {1}".format(
                    conf, repo["name"]))
            return False
        else:
            self.log.info(
                "Migrating project-level MR approval configuration for {0} (New ID: {1}) to GitLab".format(
                    repo["name"], new_id))
            self.gl_projects_api.change_project_level_mr_approval_configuration(
                new_id, self.config.destination_host, self.config.destination_token, conf)
        # migrate approval rules
        protected_branch_ids = []
        for branch in self.gl_projects_api.get_all_project_protected_branches(
                new_id, self.config.destination_host, self.config.destination_token):
            protected_branch_ids.append(branch["id"])

        des_user_ids = []
        for user in self.get_email_list_of_reviewers_for_pr(
                repo["namespace"], repo["path"]):
            if des_user := self.gl_users.find_user_by_email_comparison_without_id(
                    user):
                des_user_ids.append(des_user["id"])

        rule = self.format_project_level_mr_rule(
            new_id, protected_branch_ids, des_user_ids)

        if is_error_message_present(rule) or not rule:
            self.log.error(
                "Failed to generate MR approval rules ({0}) for project {1}".format(
                    rule, repo["name"]))
            return False
        else:
            self.gl_projects_api.create_project_level_mr_approval_rule(
                new_id, self.config.destination_host, self.config.destination_token, rule)
            return True

    def format_project_level_configuration(self, new_id, branch):
        return {
            "id": new_id,
            "approvals_before_merge": 1,
            "reset_approvals_on_push": True if branch.get(
                "required_pull_request_reviews",
                None) and branch["required_pull_request_reviews"]["dismissal_restrictions"]["users"] else False,
            "disable_overriding_approvers_per_merge_request": False,
            "merge_requests_author_approval": False,
            "merge_requests_disable_committers_approval": False,
            "require_password_to_approve": False}

    def format_project_level_mr_rule(
            self, new_id, protected_branch_ids, user_ids=None, group_ids=None):
        return{
            "name": "gh_pr_rules",
            "rule_type": "regular",
            "user_ids": user_ids,
            "group_ids": group_ids,
            "approvals_required": 1,
            "protected_branch_ids": protected_branch_ids
        }

    def transform_gh_repo_commit(self, commits):
        list_of_commits = []
        for commit in commits:
            list_of_commits.append(
                {
                    "id": commit["sha"],
                    "message": commit["message"],
                    "author_name": commit["commit"]["author"]["name"],
                    "author_email": commit["commit"]["author"]["email"],
                    "authored_date": commit["commit"]["author"]["date"],
                    "committer_name": commit["commit"]["committer"]["name"],
                    "committer_email": commit["commit"]["committer"]["email"],
                    "committed_date": commit["commit"]["committer"]["date"],
                }
            )

        return list_of_commits

    def transform_gh_branches(self, branches):
        list_of_branches = []
        for branch in branches:
            list_of_branches.append(
                {
                    "name": branch["name"],
                    "commit": {
                        "id": branch["commit"]["sha"],
                    },
                    "protected": branch["protected"],
                }
            )

        return list_of_branches

    def transform_gh_pull_requests(self, pull_requests):
        list_of_merge_requests = []
        for mr in pull_requests:
            if mr["state"] == "open":
                state = "opened"
            else:
                state = "closed"
            assignees_list = []
            if mr["assignees"]:
                for assignee in mr["assignees"]:
                    assignees_list.append(
                        {
                            "username": assignee["login"],
                        }
                    )
            list_of_merge_requests.append(
                {
                    "title": mr["title"],
                    "description": mr["head"]["repo"]["description"],
                    "state": state,
                    "created_at": mr["created_at"],
                    "updated_at": mr["updated_at"],
                    "author": {
                        "username": mr["user"]["login"],
                    },
                    "assignees": assignees_list,
                    "work_in_progress": mr["draft"],
                    "milestone": mr["milestone"],
                }
            )

        return list_of_merge_requests

    def transform_gh_tags(self, tags):
        list_of_tags = []
        for tag in tags:
            list_of_tags.append(
                {
                    "name": tag["name"],
                    "commit": {
                        "id": tag["commit"]["sha"],
                    },
                    "target": tag["commit"]["sha"]
                }
            )

        return list_of_tags

    def transform_gh_milestones(self, milestones):
        list_of_milestones = []
        for milestone in milestones:
            if milestone["state"] == "open":
                milestone_status = "active"
            else:
                milestone_status = "closed"
            list_of_milestones.append(
                {
                    "title": milestone["title"],
                    "description": milestone["description"],
                    "state": milestone_status,
                    "created_at": milestone["created_at"],
                    "updated_at": milestone["updated_at"],
                    "due_date": milestone["due_on"],
                }
            )

        return list_of_milestones

    def transform_gh_releases(self, releases):
        list_of_releases = []
        for release in releases:
            list_of_releases.append(
                {
                    "name": release["name"],
                    "tag_name": release["tag_name"],
                    "description": release["body"],
                    "created_at": release["created_at"],
                    "released_at": release["published_at"],
                    "author": {
                        "username": release["author"]["login"],
                    },
                    "upcoming_release": release["prerelease"],
                }
            )

        return list_of_releases

    def transform_gh_pr_comments(self, pr_comments):
        list_of_pr_comments = []
        for comment in pr_comments:
            list_of_pr_comments.append(
                {
                    "body": comment["body"],
                    "author": {
                        "username": comment["user"]["login"],
                    },
                    "created_at": comment["created_at"],
                    "updated_at": comment["updated_at"],
                }
            )

        return list_of_pr_comments

    def transform_gh_issues(self, issues):
        list_of_issues = []
        for issue in issues:
            labels_list = []
            for label in issue["labels"]:
                labels_list.append(label["name"])
            assignees_list = []
            for assignee in issue["assignees"]:
                assignees_list.append(assignee["login"])
            list_of_issues.append(
                {
                    "title": issue["title"],
                    "description": issue["body"],
                    "state": issue.get("state", "closed"),
                    "created_at": issue["created_at"],
                    "updated_at": issue["updated_at"],
                    "closed_at": issue["closed_at"],
                    "labels": labels_list,
                    "milestone": issue["milestone"],
                    "assignees": assignees_list,
                    "author": {
                        "username": issue["user"]["login"],
                    },
                    "assignee": issue["assignee"],
                    "user_notes_count": issue["comments"],
                    "discussion_locked": issue["locked"],
                }
            )

        return list_of_issues

    def migrate_archived_repo(self, new_id, repo):
        gh_repo = safe_json_response(
            self.repos_api.get_repo(repo["namespace"], repo["path"]))
        if gh_repo and gh_repo.get("archived", None):
            self.gl_projects_api.archive_project(
                self.config.destination_host, self.config.destination_token, new_id)
            return True
        return False

    def archive_staged_repos(self, dry_run=True):
        start = time()
        rotate_logs()
        staged_projects = self.gl_projects.get_staged_projects()
        self.log.info("Project count is: {}".format(len(staged_projects)))
        try:
            for single_project in staged_projects:
                single_project["archived"] = True
                self.log.info("{0}Archiving source project {1}".format(
                    get_dry_log(dry_run),
                    single_project["path_with_namespace"]))
                if not dry_run:
                    self.repos_api.update_repo(
                        single_project["namespace"],
                        single_project["name"],
                        single_project)
        except RequestException as re:
            self.log.error(
                "Failed to archive staged projects, with error:\n{}".format(re))
        finally:
            add_post_migration_stats(start, log=self.log)

    def get_email_list_of_reviewers_for_pr(self, owner, repo):
        user_emails_dict = {}
        start_multi_process_stream_with_args(
            self.handle_list_of_reviewers,
            self.repos_api.get_repo_pulls(
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
        mongo = self.connect_to_mongo()
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
