import json

from congregate.migration.gitlab.api.base_api import GitLabApiWrapper


class InstanceApi(GitLabApiWrapper):
    def get_all_system_hooks(self, host, token):
        """
        Get a list of all system hooks

        GitLab API Doc: https://docs.gitlab.com/ee/api/system_hooks.html#list-system-hooks

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /hooks
        """
        return self.api.list_all(host, token, "hooks")

    def add_system_hook(self, host, token, data, message=None):
        """
        Add a new system hook

        GitLab API Doc: https://docs.gitlab.com/ee/api/system_hooks.html#add-new-system-hook

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /hooks
        """
        if not message:
            message = "Creating system hook"
        return self.api.generate_post_request(host, token, "hooks", json.dumps(data), description=message)

    def get_current_license(self, host, token):
        """
        Retrieve information about the current license

        GitLab API Doc: https://docs.gitlab.com/ee/api/license.html#retrieve-information-about-the-current-license

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /license
        """
        return self.api.generate_get_request(host, token, "license")

    def get_version(self, host, token):
        """
        Version API

        GitLab API Doc: https://docs.gitlab.com/ee/api/version.html
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: JSON response containing version information from GET /version
        """
        return self.api.generate_get_request(host, token, "version")

    def get_all_instance_deploy_keys(self, host, token):
        """
        Get a list of all deploy keys across all projects of the GitLab instance. This endpoint requires admin access and is not recommended for listing on GitLab.com.

        GitLab API Doc: https://docs.gitlab.com/ee/api/deploy_keys.html#list-all-deploy-keys

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Generator returning JSON of each result from GET /deploy_keys
        """
        return self.api.list_all(host, token, "deploy_keys")

    def get_application_settings(self, host, token):
        """
        Retrieve GitLab instance application settings.

        GitLab API Doc: https://docs.gitlab.com/ee/api/settings.html#get-current-application-settings

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /application/settings
        """
        return self.api.generate_get_request(host, token, "application/settings")

    def change_application_settings(self, host, token, data, message=None):
        """
        Use an API call to modify GitLab instance application settings.

        GitLab API Doc: https://docs.gitlab.com/ee/api/settings.html#change-application-settings

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to PUT /application/settings
        """
        if not message:
            message = "Changing application settings"
        return self.api.generate_put_request(host, token, "application/settings", json.dumps(data), description=message)
