import json

from congregate.helpers import api


class SystemApi():
    def get_all_system_hooks(self, host, token):
        """
        Get a list of all system hooks

        GitLab API Doc: https://docs.gitlab.com/ee/api/system_hooks.html#list-system-hooks

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /hooks
        """
        return api.list_all(host, token, "hooks")

    def create_system_hook(self, host, token, data):
        """
        Add a new system hook

        GitLab API Doc: https://docs.gitlab.com/ee/api/system_hooks.html#add-new-system-hook

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: url: (str) The hook URL
            :return: Response object containing the response to POST /hooks
        """
        return api.generate_post_request(host, token, "hooks", json.dumps(data))

    def get_version(self, host, token):
        """
        Retrieve version information for this GitLab instance

        GitLab API Doc: https://docs.gitlab.com/ee/api/version.html

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to from GET /version
        """
        return api.generate_get_request(host, token, "version")
