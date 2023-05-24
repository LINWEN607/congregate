from json import dumps as json_dumps
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper



class SettingsAPI(GitLabApiWrapper):
    def get_application_settings(self, host, token):
        """
        List the current application settings of the GitLab instance.

        GitLab API doc: https://docs.gitlab.com/ee/api/settings.html#get-current-application-settings

            :param: host: (int) GitLab project ID
            :param: token: (str) GitLab host URL
            :return: Response object containing the response to GET /application/settings
        """
        return self.api.generate_get_request(host, token, 'application/settings')
    
    def set_application_settings(self, host, token, data):
        """
        Use an API call to modify GitLab instance application settings.

        GitLab API doc: https://docs.gitlab.com/ee/api/settings.html#change-application-settings

            :param: host: (int) GitLab project ID
            :param: token: (str) GitLab host URL
            :param: data: (dict) Application settings to update
            :return: Response object containing the response to PUT /application/settings
        """
        return self.api.generate_put_request(host, token, f"application/settings", data=json_dumps(data))
