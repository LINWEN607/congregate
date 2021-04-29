from urllib.parse import quote_plus
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper


class NamespacesApi(GitLabApiWrapper):
    def get_namespace_by_full_path(self, full_path, host, token):
        """
        Get all details of a namespace matching the full path

            :param: full_path: (string) URL encoded full path to a group
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /namespaces/<full_path>
        """
        return self.api.generate_get_request(host, token, "namespaces/{}".format(quote_plus(full_path)))
