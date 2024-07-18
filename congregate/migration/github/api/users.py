from congregate.migration.github.api.base import GitHubApi


class UsersApi():
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.api = GitHubApi(self.host, self.token)

    def get_all_users(self):
        """
        Lists all users, in the order that they signed up on GitHub. This list includes personal user accounts and organization accounts.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/users#list-users
        """
        return self.api.list_all(self.host, "users")

    def get_user(self, username):
        """
        Get the authenticated user.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/users#get-a-user
        """
        return self.api.generate_v3_get_request(self.host, f"users/{username}")

    def get_import_user(self):
        """
        Provides publicly available information about someone with a GitHub account.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/users#get-the-authenticated-user
        """
        return self.api.generate_v3_get_request(self.host, "user")

    def get_rate_limit_status(self):
        """
        Get rate limit status for the authenticated user.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/rate-limit#get-rate-limit-status-for-the-authenticated-user
        """
        return self.api.generate_v3_get_request(self.host, "rate_limit")

    def get_user_v4(self, username):
        """
        Get a user using GraphQL.
        """
        query = """
        query($login: String!) {
            user(login: $login) {
                login
                name
                url
                bio
                avatarUrl
                createdAt
            }
        }
        """
        variables = {
            "login": username
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_import_user_v4(self):
        """
        Get the authenticated user using GraphQL.
        """
        query = """
        query {
            viewer {
                login
                name
                url
                bio
                avatarUrl
                createdAt
            }
        }
        """
        return self.api.generate_v4_post_request(self.host, query)
