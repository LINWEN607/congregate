from json import dumps
from congregate.helpers.base_class import BaseClass
from congregate.helpers import api

class ImportApi(BaseClass):
    def import_from_github(self, host, token, data, message=None):
        """
        Import your projects from GitHub to GitLab via the API

        GitLab API Doc: https://docs.gitlab.com/ee/api/import.html#import-repository-from-github

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (str) Relevant data for the export (see docs above)
            :return: Response object containing the response to POST /projects/:id/unarchive

        """
        if not message:
            message = "Triggering import from GitHub"
        return api.generate_post_request(host, token, "import/github" % id, dumps(data), description=message).json()
    
    def import_from_bitbucket_server(self, host, token, data, message=None):
        """
        Import your projects from Bitbucket Server to GitLab via the API

        GitLab API Doc: https://docs.gitlab.com/ee/api/import.html#import-repository-from-bitbucket-server

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (str) Relevant data for the export (see docs above)
            :return: Response object containing the response to POST /projects/:id/unarchive

        """
        if not message:
            message = "Triggering import from BitBucket Server"
        return api.generate_post_request(host, token, "import/bitbucket_server", dumps(data), description=message).json()