from congregate.migration.github.api.base import GitHubApi


class OrgsApi():
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.api = GitHubApi(self.host, self.token)

    def get_all_orgs(self):
        return self.api.list_all(self.host, "organizations", verify=False)

    def get_org(self, org):
        return self.api.generate_v3_get_request(self.host, "orgs/{}".format(org), verify=False)

    def get_all_org_repos(self, org):
        return self.api.list_all(self.host, "orgs/{}/repos".format(org), verify=False)

    def get_all_org_members(self, org):
        return self.api.list_all(self.host, "orgs/{}/members".format(org), verify=False)

    def get_all_org_teams(self, org):
        return self.api.list_all(self.host, "orgs/{}/teams".format(org), verify=False)

    def get_all_org_team_members(self, org, team_slug):
        return self.api.list_all(self.host, "orgs/{}/teams/{}/members".format(org, team_slug), verify=False)

    def get_all_org_child_teams(self, org, team_slug):
        return self.api.list_all(self.host, "orgs/{}/teams/{}/teams".format(org, team_slug), verify=False)

    def get_all_org_child_team_members(self, org, team_slug, child_team_slug):
        return self.api.list_all(self.host, "orgs/{}/teams/{}/teams/{}/members".format(org, team_slug, child_team_slug), verify=False)
