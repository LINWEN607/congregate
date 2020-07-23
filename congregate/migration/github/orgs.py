import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes
from congregate.migration.github.api.orgs import OrgsApi


class OrgsClient(BaseClass):
    def __init__(self):
        super(OrgsClient, self).__init__()
        self.orgs_api = OrgsApi(self.config.source_host,
                                self.config.source_token)

    def get_orgs(self):
        with open("{}/data/groups.json".format(self.app_path), "r") as f:
            return json.load(f)

    def retrieve_org_info(self):
        orgs = self.orgs_api.get_all_orgs()
        for org in orgs:
            org["teams"] = self.orgs_api.get_all_org_teams(org["login"])
            org["repos"] = self.orgs_api.get_all_org_repos(org["login"])
            org["members"] = self.orgs_api.get_all_org_members(org["login"])
            for team in org["teams"]:
                team["child_teams"] = self.orgs_api.get_all_org_child_teams(
                    org["login"], team["name"])
                team["repos"] = self.orgs_api.get_all_org_team_repos(
                    org["login"], team["name"])
                team["members"] = self.orgs_api.get_all_org_team_members(
                    org["login"], team["name"])
                for child_team in team["child_teams"]:
                    child_team["repos"] = self.orgs_api.get_all_org_child_team_repos(
                        org["login"], team["name"], child_team["name"])
                    child_team["members"] = self.orgs_api.get_all_org_child_team_members(
                        org["login"], team["name"], child_team["name"])
        with open("{}/data/groups.json".format(self.app_path), "w") as f:
            json.dump(remove_dupes(orgs), f, indent=4)
        return remove_dupes(orgs)
