from congregate.migration.gitlab.api.base_api import GitLabApiWrapper

class SnippetsApi(GitLabApiWrapper):

    def get_public_snippets(self, host, token):
        """
        List all public snippets

        GitLab API Doc: https://docs.gitlab.com/ee/api/snippets.html#list-all-public-snippets

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /snippets/public
        """
        return self.api.list_all(host, token, "snippets/public")
