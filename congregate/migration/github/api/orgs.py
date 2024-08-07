from congregate.migration.github.api.base import GitHubApi
from congregate.helpers.conf import Config
from gitlab_ps_utils.misc_utils import safe_json_response


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

    def get_all_org_repos(self, org, page_check=True):
        """
        Lists repositories for the specified organization.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-organization-repositories
        """
        return self.api.list_all(self.host, "orgs/{}/repos".format(org), page_check=page_check)

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
    
    def get_all_orgs_v4(self):
        """
        Lists all organizations using GraphQL.
        """
        query = """
        query($cursor: String) {
            viewer {
                organizations(first: 100, after: $cursor) {
                    nodes {
                        login
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
        """
        variables = {
            "cursor": None
        }

        all_orgs = []
        while True:
            response = safe_json_response(self.api.generate_v4_post_request(self.host, query, variables))
            if response and 'data' in response:
                orgs_data = response['data']['viewer']['organizations']
                all_orgs.extend(orgs_data['nodes'])
                if orgs_data['pageInfo']['hasNextPage']:
                    variables['cursor'] = orgs_data['pageInfo']['endCursor']
                else:
                    break
            else:
                break

        return all_orgs

    def get_org_v4(self, org):
        """
        Get an organization.

        Using GraphQL API
        """
        query = """
        query($login: String!) {
            organization(login: $login) {
                id
                login
                description
            }
        }
        """
        variables = {
            "login": org
        }

        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_all_org_repos_v4(self, org):
        """
        Lists repositories for the specified organization using GraphQL.
        """
        query = """
        query($login: String!, $cursor: String) {
            organization(login: $login) {
                repositories(first: 100, after: $cursor) {
                    nodes {
                        id
                        name
                        description
                        url
                        nameWithOwner
                        visibility
                        owner {
                            id
                            login
                            __typename
                        }
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
        """
        variables = {
            "login": org,
            "cursor": None
        }

        all_repos = []
        while True:
            response = safe_json_response(self.api.generate_v4_post_request(self.host, query, variables))
            if response and 'data' in response:
                repos_data = response['data']['organization']['repositories']
                all_repos.extend(repos_data['nodes'])
                if repos_data['pageInfo']['hasNextPage']:
                    variables['cursor'] = repos_data['pageInfo']['endCursor']
                else:
                    break
            else:
                break

        return all_repos

    def get_all_org_members_v4(self, org):
        """
        Lists all users who are members of an organization using GraphQL.
        """
        query = """
        query($login: String!, $cursor: String) {
            organization(login: $login) {
                membersWithRole(first: 100, after: $cursor) {
                    nodes {
                        login
                        name
                        url
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
        """
        variables = {
            "login": org,
            "cursor": None
        }

        all_members = []
        while True:
            response = safe_json_response(self.api.generate_v4_post_request(self.host, query, variables))
            if response and 'data' in response:
                members_data = response['data']['organization']['membersWithRole']
                all_members.extend(members_data['nodes'])
                if members_data['pageInfo']['hasNextPage']:
                    variables['cursor'] = members_data['pageInfo']['endCursor']
                else:
                    break
            else:
                break

        return all_members

    def get_all_org_teams_v4(self, org):
        """
        Lists all teams in an organization using GraphQL.
        """
        query = """
        query($login: String!, $cursor: String) {
            organization(login: $login) {
                teams(first: 100, after: $cursor) {
                    nodes {
                        slug
                        name
                        url
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
        """
        variables = {
            "login": org,
            "cursor": None
        }

        all_teams = []
        while True:
            response = safe_json_response(self.api.generate_v4_post_request(self.host, query, variables))
            if response and 'data' in response:
                teams_data = response['data']['organization']['teams']
                all_teams.extend(teams_data['nodes'])
                if teams_data['pageInfo']['hasNextPage']:
                    variables['cursor'] = teams_data['pageInfo']['endCursor']
                else:
                    break
            else:
                break

        return all_teams

    def get_org_team_v4(self, org, team_slug):
        """
        Gets a team using the team's slug.

        Using GraphQL API
        """
        query = """
        query($login: String!, $slug: String!) {
            organization(login: $login) {
                team(slug: $slug) {
                    slug
                    name
                    url
                }
            }
        }
        """
        variables = {
            "login": org,
            "slug": team_slug
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_all_org_team_repos_v4(self, org, team_slug):
        """
        Lists a team's repositories.

        Using GraphQL API
        """
        query = """
        query($login: String!, $slug: String!, $limit: Int!) {
            organization(login: $login) {
                team(slug: $slug) {
                    repositories(first: $limit) {
                        nodes {
                            name
                            description
                            url
                        }
                    }
                }
            }
        }
        """
        variables = {
            "login": org,
            "slug": team_slug,
            "limit": 100
        }
        return self.api.list_all_v4(self.host, query, variables)

    def get_all_org_team_members_v4(self, org, team_slug):
        """
        Lists members of a team.

        Using GraphQL API
        """
        query = """
        query($login: String!, $slug: String!, $limit: Int!) {
            organization(login: $login) {
                team(slug: $slug) {
                    members(first: $limit) {
                        nodes {
                            login
                            name
                            url
                        }
                    }
                }
            }
        }
        """
        variables = {
            "login": org,
            "slug": team_slug,
            "limit": 100
        }
        return self.api.list_all_v4(self.host, query, variables)

    def get_all_org_child_teams_v4(self, org, team_slug):
        """
        Lists the child teams of a team.

        Using GraphQL API
        """
        query = """
        query($login: String!, $slug: String!, $limit: Int!) {
            organization(login: $login) {
                team(slug: $slug) {
                    childTeams(first: $limit) {
                        nodes {
                            slug
                            name
                            url
                        }
                    }
                }
            }
        }
        """
        variables = {
            "login": org,
            "slug": team_slug,
            "limit": 100
        }
        return self.api.list_all_v4(self.host, query, variables)
