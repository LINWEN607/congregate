from gitlab_ps_utils.misc_utils import safe_json_response, is_error_message_present, strip_netloc
from gitlab_ps_utils.dict_utils import dig

from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector
from congregate.helpers.utils import is_github_dot_com
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
        self.host = strip_netloc(host)

    def retrieve_org_info(self, processes=None):
        """
        Extend list of already formatted public repos with org and team repos.
        While traversing orgs gather repo, team and member metadata.
        """
        groups = []
        if is_github_dot_com(
                self.config.source_host) and self.config.src_parent_org:
            orgs = [safe_json_response(
                self.orgs_api.get_org_v4(self.config.src_parent_org))]
        else:
            orgs = self.orgs_api.get_all_orgs_v4()
        self.multi.start_multi_process_stream_with_args(
            self.handle_org_retrieval, orgs, groups, processes=processes, nestable=True)

    def handle_org_retrieval(self, groups, org):
        mongoclient = CongregateMongoConnector()
        self.add_org_as_group(groups, org["data"]["organization"]["login"], mongoclient)
        for team in self.orgs_api.get_all_org_teams_v4(org["data"]["organization"]["login"]):
            self.add_team_as_subgroup(
                org, team, mongoclient)
        mongoclient.close_connection()

    def add_org_as_group(self, groups, org_name, mongo):
        org = safe_json_response(self.orgs_api.get_org_v4(org_name))
        is_error, org = is_error_message_present(org)
        if groups is None or is_error or not org:
            self.log.error(
                f"Failed to append org {org_name} ({org}) to list {groups}")
        else:
            org_repos = []
            for org_repo in self.orgs_api.get_all_org_repos_v4(
                    org_name):
                org_repo['owner']['id'] = org["data"]["organization"]["databaseId"]
                formatted_repo = self.repos.format_repo(org_repo, mongo)
                mongo.insert_data(
                    f"projects-{self.host}", formatted_repo)
                formatted_repo.pop("_id")
                formatted_repo["members"] = []
                # Save all org repos ID references as part of group metadata
                org_repos.append(formatted_repo.get("id"))
            members = self.add_org_members([], org, mongo)
            mongo.insert_data(f"groups-{self.host}", {
                "name": org["data"]["organization"]["login"],
                "id": org["data"]["organization"]["databaseId"],
                "path": org["data"]["organization"]["login"],
                "full_path": org["data"]["organization"]["login"],
                "description": org["data"]["organization"].get("description", ""),
                "visibility": "private",   # No mapping field
                "parent_id": None,   # top-level group
                "auto_devops_enabled": False,
                "members": members,
                # "projects": self.repos.format_repos([], org_repos, org=True)
                "projects": org_repos
            })
        return groups

    def add_team_as_subgroup(self, org, team, mongo):
        error, team = is_error_message_present(team)
        if error or not team:
            self.log.error(f"Failed to store team '{team}'")
        else:
            org_name = org["data"]["organization"]["login"]
            if self.get_team_full_path(org_name, team):
                for team_repo in self.teams_api.get_team_repos_v4(org_name, team["slug"]):
                    formatted_repo = self.repos.format_repo(team_repo, mongo)
                    mongo.insert_data(
                        f"projects-{self.host}", formatted_repo)
                    # TODO: Actually add teams as subgroups to "groups-" in mongo?

    def get_team_full_path(self, org_name, team):
        """
        Traverse org teams in order to construct the full path.
        Teams can have N levels of nested teams i.e. child teams.
        E.g. the full path could be org1/team1/child_team1/.../child_teamN.
        Assume the parent org at the beginning and child_teamN at the end of the full path.
        """
        try:
            full_path = [org_name, team["slug"]]
            while team["parentTeam"]:
                full_path.insert(1, dig(team, 'parentTeam', 'slug'))
                team = safe_json_response(self.orgs_api.get_org_team_v4(
                    org_name, dig(team, 'parentTeam', 'slug')))
                error, team = is_error_message_present(team)
                if error or not team:
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
        for m in self.orgs_api.get_all_org_members_v4(org["data"]["organization"]["login"]):
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
