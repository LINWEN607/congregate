from congregate.migration.github.api.base import GitHubApi
from congregate.helpers.conf import Config


class TeamsApi():
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.api = GitHubApi(self.host, self.token)
        self.config = Config()

    def get_team_repos(self, team_id):
        """
        List team repositories.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repository-teams
        """
        return self.api.list_all(self.host, f"teams/{team_id}/repos")

    def get_team_members(self, team_id):
        """
        List team members.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/teams#list-team-members-legacy
        """
        return self.api.list_all(self.host, f"teams/{team_id}/members")

    def get_team_repos_v4(self, org, team_slug):
        """
        List team repositories using GraphQL.
        """
        query = """
        query($org: String!, $teamSlug: String!, $cursor: String) {
            organization(login: $org) {
                team(slug: $teamSlug) {
                    repositories(first: 100, after: $cursor) {
                        nodes {
                            id
                            name
                            description
                            url
                            owner {
                                login
                                id
                                __typename
                            }
                            isPrivate
                            visibility
                            nameWithOwner
                            isArchived
                        }
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                    }
                }
            }
        }
        """
        variables = {
            "org": org,
            "teamSlug": team_slug,
            "cursor": None
        }

        all_repos = []
        while True:
            response = self.api.generate_v4_post_request(self.host, query, variables)
            if response and 'data' in response:
                repos_data = response['data']['organization']['team']['repositories']
                all_repos.extend(repos_data['nodes'])
                if repos_data['pageInfo']['hasNextPage']:
                    variables['cursor'] = repos_data['pageInfo']['endCursor']
                else:
                    break
            else:
                break

        return all_repos

    def get_team_members_v4(self, org, team_slug):
        """
        List team members using GraphQL.
        """
        query = """
        query($org: String!, $teamSlug: String!) {
            organization(login: $org) {
                team(slug: $teamSlug) {
                    members(first: 100) {
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
            "org": org,
            "teamSlug": team_slug
        }
        return self.api.generate_v4_post_request(self.host, query, variables)
