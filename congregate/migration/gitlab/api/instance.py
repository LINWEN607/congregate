import json

from congregate.helpers import api


class InstanceApi():
    def get_all_instance_hooks(self, host, token):
        """
        Get a list of all instance hooks

        GitLab API Doc: https://docs.gitlab.com/ee/api/system_hooks.html#list-system-hooks

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /hooks
        """
        return api.list_all(host, token, "hooks")

    def add_instance_hook(self, host, token, data, message=None):
        """
        Add a new instance hook

        GitLab API Doc: https://docs.gitlab.com/ee/api/system_hooks.html#add-new-system-hook

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /hooks
        """
        if not message:
            message = "Creating instance hook"
        return api.generate_post_request(host, token, "hooks", json.dumps(data), description=message)

    def get_all_instance_clusters(self, host, token):
        """
        Returns a list of instance clusters

        GitLab API Doc: https://docs.gitlab.com/ee/api/instance_clusters.html#list-instance-clusters

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /admin/clusters
        """
        return api.list_all(host, token, "admin/clusters")

    def add_instance_cluster(self, host, token, data, message=None):
        """
        Adds an existing Kubernetes instance cluster

        GitLab API Doc: https://docs.gitlab.com/ee/api/instance_clusters.html#add-existing-instance-cluster

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /admin/clusters/add
        """
        if not message:
            message = "Creating instance cluster"
        return api.generate_post_request(host, token, "admin/clusters/add", json.dumps(data), description=message)

    def get_current_license(self, host, token):
        """
        Retrieve information about the current license

        GitLab API Doc: https://docs.gitlab.com/ee/api/license.html#retrieve-information-about-the-current-license

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /license
        """
        return api.generate_get_request(host, token, "license")
