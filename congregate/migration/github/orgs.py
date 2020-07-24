import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes
from congregate.migration.github.api.orgs import OrgsApi


class OrgsClient(BaseClass):
    def __init__(self):
        super(OrgsClient, self).__init__()
        self.orgs_api = OrgsApi(self.config.source_host,
                                self.config.source_token)

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
        orgs = self.orgs_api.get_all_orgs()
        for org in orgs:
            org["repos"] = self.orgs_api.get_all_org_repos(org["login"])
            repos.extend(org["repos"])
            org["members"] = self.orgs_api.get_all_org_members(org["login"])
            org["teams"] = self.orgs_api.get_all_org_teams(org["login"])
            for team in org["teams"]:
                team["child_teams"] = self.orgs_api.get_all_org_child_teams(
                    org["login"], team["name"])
                team["repos"] = self.orgs_api.get_all_org_team_repos(
                    org["login"], team["name"])
                repos.extend(team["repos"])
                team["members"] = self.orgs_api.get_all_org_team_members(
                    org["login"], team["name"])
        with open("{}/data/groups.json".format(self.app_path), "w") as f:
            json.dump(remove_dupes(orgs), f, indent=4)
        with open("{}/data/project_json.json".format(self.app_path), "w") as f:
            json.dump(remove_dupes(repos), f, indent=4)
        return remove_dupes(orgs)
