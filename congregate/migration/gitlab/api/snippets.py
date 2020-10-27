import json

from congregate.helpers import api

class SnippetsApi():

    def get_public_snippets(self, host, token):
        """
        List all public snippets

        GitLab API Doc: https://docs.gitlab.com/ee/api/snippets.html#list-all-public-snippets

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /snippets/public
        """
        return api.list_all(host, token, "snippets/public")
