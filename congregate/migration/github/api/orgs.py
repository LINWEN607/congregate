from congregate.migration.github.api.base import GitHubApi
from congregate.helpers.conf import Config


class OrgsApi():
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.api = GitHubApi(self.host, self.token)
        self.config = Config()

    def get_all_orgs(self):
        """
        Lists all organizations, in the order that they were created on GitHub Enterprise.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/orgs#list-organizations
        """
        return self.api.list_all(self.host, "organizations")

    def get_org(self, org):
        """
        Get an organization

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/orgs#get-an-organization
        """
        return self.api.generate_v3_get_request(self.host, "orgs/{}".format(org))

    def get_all_org_repos(self, org):
        """
        Lists repositories for the specified organization.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-organization-repositories
        """
        return self.api.list_all(self.host, "orgs/{}/repos".format(org))

    def get_all_org_members(self, org):
        """
        List all users who are members of an organization.
        If the authenticated user is also a member of this organization then both concealed and public members will be returned.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/orgs#list-organization-members
        """
        return self.api.list_all(self.host, "orgs/{}/members".format(org))

    def get_all_org_teams(self, org):
        """
        Lists all teams in an organization that are visible to the authenticated user.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/teams#list-teams
        """
        return self.api.list_all(self.host, "orgs/{}/teams".format(org))

    def get_org_team(self, org, team_slug):
        """
        Gets a team using the team's slug. GitHub generates the slug from the team name.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/teams#get-a-team-by-name
        """
        return self.api.generate_v3_get_request(self.host, "orgs/{}/teams/{}".format(org, team_slug))

    def get_all_org_team_repos(self, org, team_slug):
        """
        Lists a team's repositories visible to the authenticated user.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/teams#list-team-repositories
        """
        return self.api.list_all(self.host, "orgs/{}/teams/{}/repos".format(org, team_slug))

    def get_all_org_team_members(self, org, team_slug):
        """
        Team members will include the members of child teams.
        To list members in a team, the team must be visible to the authenticated user.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/teams#list-team-members
        """
        return self.api.list_all(self.host, "orgs/{}/teams/{}/members".format(org, team_slug))

    def get_all_org_child_teams(self, org, team_slug):
        """
        Lists the child teams of the team requested by :team_slug.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/teams#list-child-teams
        """
        return self.api.list_all(self.host, "orgs/{}/teams/{}/teams".format(org, team_slug))

    def create_org(self, data=None, message=None):
        """
        Create an organization.

        GitHub API v3 Doc: https://docs.github.com/en/enterprise/2.21/user/rest/reference/enterprise-admin#create-an-organization
        """
        if not message:
            print(f"Creating an organization {data}")

        return self.api.generate_v3_post_request(
            self.host,
            "admin/organizations",
            data,
            description=message
        )
