from congregate.migration.github.api.base import GitHubApi
from congregate.helpers.conf import Config

class GistsApi():
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.api = GitHubApi(self.host, self.token)
        self.config = Config()

    def get_public_gists(self):
        """
        List public gists.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/gists#list-public-gists
        """
        return self.api.list_all(self.host, "gists/public")

    def get_single_gist(self, gist_id):
        """
        List single gist.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/gists#get-a-gist
        """
        return self.api.list_all(self.host, f"gists/{gist_id}")

    def get_public_gists_v4(self):
        """
        List public gists.

        Using GraphQL API
        """
        query = """
        query($limit: Int!) {
            viewer {
                gists(first: $limit, privacy: PUBLIC) {
                    nodes {
                        id
                        description
                        url
                        files {
                            name
                            text
                        }
                    }
                }
            }
        }
        """
        variables = {
            "limit": 100
        }
        return self.api.list_all(self.host, query, variables)

    def get_single_gist_v4(self, gist_id):
        """
        Get a single gist by ID.

        Using GraphQL API
        """
        query = """
        query($id: ID!) {
            node(id: $id) {
                ... on Gist {
                    id
                    description
                    url
                    files {
                        name
                        text
                    }
                }
            }
        }
        """
        variables = {
            "id": gist_id
        }
        return self.api.list_all(self.host, query, variables)
