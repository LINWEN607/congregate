from json import dumps
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper

class ImportApi(GitLabApiWrapper):

    def import_from_github(self, host, token, data, message=None):
        """
        Import your projects from GitHub to GitLab via the API

        GitLab API Doc: https://docs.gitlab.com/ee/api/import.html#import-repository-from-github

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (str) Relevant data for the export (see docs above)
            :return: Response object containing the response to POST /import/github

        """
        if not message:
            audit_data = data.copy()
            audit_data.pop("personal_access_token", None)
            message = f"Triggering import from GitHub with payload {audit_data}"
        return self.api.generate_post_request(host, token, "import/github", dumps(data), description=message).json()

    def import_from_bitbucket_server(self, host, token, data, message=None):
        """
        Import your projects from Bitbucket Server to GitLab via the API

        GitLab API Doc: https://docs.gitlab.com/ee/api/import.html#import-repository-from-bitbucket-server

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (str) Relevant data for the export (see docs above)
            :return: Response object containing the response to POST /import/bitbucket_server

        """
        if not message:
            audit_data = data.copy()
            audit_data.pop("personal_access_token", None)
            message = f"Triggering import from BitBucket Server with payload {audit_data}"
        return self.api.generate_post_request(
            host,
            token,
            "import/bitbucket_server",
            dumps(data),
            description=message
        ).json()
    
    def import_from_azure(self, host, token, data, message=None):
        """
        Import your projects from Azure Devops to GitLab via the API

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#create-project

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (str) Relevant data for the export (see docs above)
            :return: Response object containing the response to POST /import/bitbucket_server

        """
        if not message:
            audit_data = data.copy()
            audit_data.pop("personal_access_token", None)
            message = f"Triggering import from Azure Devops with payload {audit_data}"
        return self.api.generate_post_request(
            host,
            token,
            "projects",
            dumps(data),
            description=message
        ).json()