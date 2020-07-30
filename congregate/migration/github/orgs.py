import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes
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
        repos = self.get_formatted_repos()
        obj = []
        for org in self.orgs_api.get_all_orgs():
            self.add_orgs_as_groups(obj, org["login"], repos)
            for team in self.orgs_api.get_all_org_teams(org["login"]):
                self.add_teams_as_subgroups(
                    obj, org["login"], team, repos)
        with open("{}/data/groups.json".format(self.app_path), "w") as f:
            json.dump(remove_dupes(obj), f, indent=4)
        with open("{}/data/project_json.json".format(self.app_path), "w") as f:
            json.dump(remove_dupes(repos), f, indent=4)
        return remove_dupes(obj)

    def add_orgs_as_groups(self, obj, org_name, repos):
        org_repos = self.orgs_api.get_all_org_repos(org_name)
        # repos.extend(self.repos.format_repos(org_repos))
        org = self.orgs_api.get_org(org_name).json()
        obj.append({
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
            "projects": []   # self.repos.format_repos(org_repos),
        })
        return obj

    def add_teams_as_subgroups(self, obj, org_name, team, repos):
        team_repos = self.orgs_api.get_all_org_team_repos(
            org_name, team["slug"])
        # repos.extend = self.repos.format_repos(team_repos)
        obj.append({
            "name": team["name"],
            "id": team["id"],
            "path": team["slug"],
            "full_path": self.get_team_full_path(org_name, team),
            "description": team.get("description", ""),
            "visibility": "private" if team["privacy"] == "secret" else "public",
            # parent group
            "parent_id": team["parent"]["id"] if team.get("parent", None) else None,
            "auto_devops_enabled": False,
            # self.users.format_users(self.orgs_api.get_all_org_team_members(org_name, team["slug"])),
            "members": [],
            "projects": []   # self.repos.format_repos(team_repos),
        })

    def get_team_full_path(self, org_name, team):
        full_path = [org_name, team["slug"]]
        while team["parent"]:
            full_path.insert(1, team["parent"]["slug"])
            team = self.orgs_api.get_org_team(
                org_name, team["parent"]["slug"]).json()
        return "/".join(full_path)
