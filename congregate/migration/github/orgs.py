import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes, safe_json_response, is_error_message_present, json_pretty
from congregate.migration.github.api.orgs import OrgsApi
from congregate.migration.github.repos import ReposClient
from congregate.migration.github.users import UsersClient


class OrgsClient(BaseClass):
    def __init__(self):
        super(OrgsClient, self).__init__()
        self.orgs_api = OrgsApi(self.config.source_host,
                                self.config.source_token)
        self.repos = ReposClient()
        self.users = UsersClient()

    def get_formatted_repos(self):
        """
        Get list of already formatted public repos.
        """
        with open("{}/data/project_json.json".format(self.app_path), "r") as f:
            return json.load(f)

    def retrieve_org_info(self):
        """
        Extend list of already formatted public repos with org and team repos.
        While traversing orgs gather repo, team and member metadata.
        """
        projects = self.get_formatted_repos()
        groups = []

        # Create tree structure {"GROUP": {"PROJECTS": [], "SUB-GROUPS": [{"FULL_PATH": "", "PROJECTS": []}]}}
        tree = {}
        for org in self.orgs_api.get_all_orgs():
            tree.update({org["login"]: {"PROJECTS": [], "SUB-GROUPS": []}})
            self.add_org_as_group(groups, org["login"], projects, tree=tree)
            for team in self.orgs_api.get_all_org_teams(org["login"]):
                self.add_team_as_subgroup(
                    groups, org["login"], team, projects, tree=tree)
        with open("{}/data/groups.json".format(self.app_path), "w") as f:
            json.dump(remove_dupes(groups), f, indent=4)
        with open("{}/data/project_json.json".format(self.app_path), "w") as f:
            json.dump(remove_dupes(projects), f, indent=4)
        self.log.info("Group tree structure:\n{}".format(json_pretty(tree)))
        return remove_dupes(groups)

    def add_org_as_group(self, groups, org_name, projects, tree=None):
        org = safe_json_response(self.orgs_api.get_org(org_name))
        if groups is None or is_error_message_present(org):
            self.log.error(
                "Failed to append org {} ({}) to list {}".format(org_name, org, groups))
        else:
            org_repos = self.orgs_api.get_all_org_repos(org_name)
            if tree:
                tree[org_name]["PROJECTS"] = [r["full_name"]
                                              for r in org_repos]
            self.repos.format_repos(projects, org_repos)
            groups.append({
                "name": org["login"],
                "id": org["id"],
                "path": org["login"],
                "full_path": org["login"],
                "description": org.get("description", ""),
                "visibility": "private",   # No mapping field
                "parent_id": None,   # top-level group
                "auto_devops_enabled": False,
                # self.users.format_users(self.orgs_api.get_all_org_members(org_name)),
                "members": [],
                "projects": self.repos.format_repos([], org_repos)
            })
        return groups, projects

    def add_team_as_subgroup(self, groups, org_name, team, projects, tree=None):
        if groups is None or is_error_message_present(team):
            self.log.error(
                "Failed to append team ({}) to list {}".format(team, groups))
        else:
            full_path = self.get_team_full_path(org_name, team)
            team_repos = self.orgs_api.get_all_org_team_repos(
                org_name, team["slug"])
            if tree:
                tree[org_name]["SUB-GROUPS"].append({"FULL_PATH": full_path, "PROJECTS": [
                                                    r["full_name"] for r in team_repos]})
            self.repos.format_repos(projects, team_repos)
            groups.append({
                "name": team["name"],
                "id": team["id"],
                "path": team["slug"],
                "full_path": full_path,
                "description": team.get("description", ""),
                "visibility": "private" if team["privacy"] == "secret" else "public",
                # parent group
                "parent_id": team["parent"]["id"] if team.get("parent", None) else None,
                "auto_devops_enabled": False,
                # self.users.format_users(self.orgs_api.get_all_org_team_members(org_name, team["slug"])),
                "members": [],
                "projects": self.repos.format_repos([], team_repos)
            })
        return groups, projects

    def get_team_full_path(self, org_name, team):
        """
        Traverse org teams in order to construct the full path.
        Teams can have N levels of nested teams i.e. child teams.
        E.g. the full path could be org1/team1/child_team1/.../child_teamN.
        Assume the parent org at the beginning and child_teamN at the end of the full path.
        """
        full_path = [org_name, team["slug"]]
        while team["parent"]:
            full_path.insert(1, team["parent"]["slug"])
            team = safe_json_response(self.orgs_api.get_org_team(
                org_name, team["parent"]["slug"]))
            if is_error_message_present(team):
                self.log.error(
                    "Failed to get full_path for team ({})".format(team))
                return None
        return "/".join(full_path)
