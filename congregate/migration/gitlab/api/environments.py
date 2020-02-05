import json
from congregate.helpers import api

class EnvironmentsApi():

    def get_environment(self, project_id, env_id, host, token):
        """
        Get a specific environment
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html#get-a-specific-environment

            :param: project_id: (int) GitLab project ID
            :param: env_id: (int) GitLab project environment ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/:id/environments/:environment_id

        """
        return api.generate_get_request(host, token, "projects/{0}/environments/{1}".format(project_id, env_id))

    def get_all_environments(self, project_id, host, token):
        """
        Get a specific environment
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html#get-a-specific-environment

            :param: project_id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: RGenerator returning JSON of each result from GET /projects/:id/environments

        """
        return api.list_all(host, token, "projects/{}/environments".format(project_id))

    def create_environment(self, host, token, project_id, data):
        """
        Creates a new environment
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html#create-a-new-environment

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: project_id: (str) GitLab project ID
            :param: data: (dict) Object containing the necessary data for creating an environment. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:id/environments

        """
        return api.generate_post_request(host, token, "projects/{}/environments".format(project_id), json.dumps(data))

    def delete_environment(self, project_id, env_id, host, token):
        """
        Delete a project environment

        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html#delete-an-environment

            :param: project_id: (int) GitLab project ID
            :param: env_id: (int) GitLab project environment ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 204 (No Content) or 404 (Group not found) from DELETE /projects/:id/environments/:environment_id
        """
        return api.generate_delete_request(host, token, "projects/{0}/environments/{1}".format(project_id, env_id))
