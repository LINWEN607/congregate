import json

from congregate.helpers import api

class VersionApi():

    def get_verison(self, host, token):
        """
        Version API

        GitLab API Doc: https://docs.gitlab.com/ee/api/version.html
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: JSON response containing version information from GET /version
        """
        return api.generate_get_request(host, token, "version")