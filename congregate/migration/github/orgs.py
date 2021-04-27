import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import safe_json_response, is_error_message_present, strip_protocol
from congregate.helpers.dict_utils import dig
from congregate.helpers.utils import is_github_dot_com
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.processes import start_multi_process_stream_with_args
from congregate.migration.github.api.orgs import OrgsApi
from congregate.migration.github.api.teams import TeamsApi
from congregate.migration.github.repos import ReposClient
from congregate.migration.github.users import UsersClient


class OrgsClient(BaseClass):
    ORG_PERMISSIONS_MAP = {
        "admin": 50,  # Owner
        "write": 30,  # Developer
        "read": 20,  # Reporter
        "none": 10,  # Guest
        None: 10  # in case of no "default_repository_permission" field
    }

    # Deprecated, but used due to no current alternative
    TEAM_PERMISSIONS_MAP = {
        "admin": 50,  # Owner
        "push": 30,  # Developer
        "pull": 20,  # Reporter
        None: 10,  # Guest, in case of no "permission" field
    }

    def __init__(self, host, token):
        super().__init__()
        self.orgs_api = OrgsApi(host, token)
        self.teams_api = TeamsApi(host, token)
        self.repos = ReposClient(host, token)
        self.users = UsersClient(host, token)
        self.host = strip_protocol(host)

    def connect_to_mongo(self):
        return MongoConnector()

    def get_formatted_repos(self):
        """
        Get list of already formatted public repos.
        """
        with open("{}/data/projects.json".format(self.app_path), "r") as f:
            return json.load(f)

    def retrieve_org_info(self, processes=None):
        """
        Extend list of already formatted public repos with org and team repos.
        While traversing orgs gather repo, team and member metadata.
        """
        groups = []
        if is_github_dot_com(
                self.config.source_host) and self.config.src_parent_org:
            orgs = [safe_json_response(
                self.orgs_api.get_org(self.config.src_parent_org))]
        else:
            orgs = self.orgs_api.get_all_orgs()
        start_multi_process_stream_with_args(
            self.handle_org_retrieval, orgs, groups, processes=processes)

    def handle_org_retrieval(self, groups, org):
        mongoclient = self.connect_to_mongo()
        self.add_org_as_group(groups, org["login"], mongoclient)
        for team in self.orgs_api.get_all_org_teams(org["login"]):
            self.add_team_as_subgroup(
                org, team, mongoclient)
        mongoclient.close_connection()

    def add_org_as_group(self, groups, org_name, mongo):
        org = safe_json_response(self.orgs_api.get_org(org_name))
        if groups is None or is_error_message_present(org):
            self.log.error(
                "Failed to append org {} ({}) to list {}".format(org_name, org, groups))
        else:
            org_repos = []
            for org_repo, _ in self.orgs_api.get_all_org_repos(
                    org_name, page_check=True):
                formatted_repo = self.repos.format_repo(org_repo, mongo)
                mongo.insert_data(f"projects-{self.host}", formatted_repo)
                formatted_repo.pop("_id")
                formatted_repo["members"] = []
                org_repos.append(formatted_repo)
            members = self.add_org_members([], org, mongo)
            mongo.insert_data(f"groups-{self.host}", {
                "name": org["login"],
                "id": org["id"],
                "path": org["login"],
                "full_path": org["login"],
                "description": org.get("description", ""),
                "visibility": "private",   # No mapping field
                "parent_id": None,   # top-level group
                "auto_devops_enabled": False,
                "members": members,
                # "projects": self.repos.format_repos([], org_repos, org=True)
                "projects": org_repos
            })
        return groups

    def add_team_as_subgroup(self, org, team, mongo):
        if is_error_message_present(team):
            self.log.error(
                "Failed to store team {}".format(team))
        else:
            org_name = org.get("login")
            if self.get_team_full_path(org_name, team):
                team_repos = []
                for team_repo in self.teams_api.get_team_repos(team["id"]):
                    formatted_repo = self.repos.format_repo(team_repo, mongo)
                    mongo.insert_data(f"projects-{self.host}", formatted_repo)
                    formatted_repo.pop("_id")
                    formatted_repo["members"] = []
                    team_repos.append(formatted_repo)

    def get_team_full_path(self, org_name, team):
        """
        Traverse org teams in order to construct the full path.
        Teams can have N levels of nested teams i.e. child teams.
        E.g. the full path could be org1/team1/child_team1/.../child_teamN.
        Assume the parent org at the beginning and child_teamN at the end of the full path.
        """
        try:
            full_path = [org_name, team["slug"]]
            while team["parent"]:
                full_path.insert(1, dig(team, 'parent', 'slug'))
                team = safe_json_response(self.orgs_api.get_org_team(
                    org_name, dig(team, 'parent', 'slug')))
                if not team or is_error_message_present(team):
                    self.log.error(
                        "Failed to get full_path for team ({})".format(team))
                    return None
            return "/".join(full_path)
        except ValueError:
            self.log.error("Unable to find")
            return None

    def add_org_members(self, members, org, mongo):
        permissions = self.ORG_PERMISSIONS_MAP[org.get(
            "default_repository_permission", None)]
        for m in self.orgs_api.get_all_org_members(org["login"]):
            m["permissions"] = permissions
            members.append(m)
        return self.users.format_users(members, mongo)

    def add_team_members(self, members, team, mongo):
        permissions = self.TEAM_PERMISSIONS_MAP[team.get("permission", None)]
        for m in self.teams_api.get_team_members(team["id"]):
            m["permissions"] = permissions
            members.append(m)
        return self.users.format_users(members, mongo)

    def transform_gh_org_repos(self, repositories):
        list_of_repos = []
        for repo in repositories:
            if repo["private"]:
                visibility = "private"
            else:
                # Need to determine if we should use public or internal
                visibility = "internal"
            list_of_repos.append(
                {
                    "description": repo["description"],
                    "name": repo["name"],
                    "name_with_namespace": repo["full_name"],
                    "created_at": repo["created_at"],
                    "default_branch": repo["default_branch"],
                    "forks_count": repo["forks"],
                    "star_count": repo["stargazers_count"],
                    "last_activity_at": repo["updated_at"],
                    "archived": repo["archived"],
                    "visibility": visibility,
                    "issues_enabled": repo["has_issues"],
                    "wiki_enabled": repo["has_wiki"],
                    "open_issues_count": repo["open_issues_count"],
                }
            )

        return list_of_repos
