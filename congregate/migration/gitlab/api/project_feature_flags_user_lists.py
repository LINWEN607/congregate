from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
import json


class ProjectFeatureFlagsUserListsApi(GitLabApiWrapper):
    def get_all_project_feature_flag_user_lists(self, host, token, project_id):
        """
        Get a list of feature flag user lists for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/feature_flag_user_lists.html#list-all-feature-flag-user-lists-for-a-project

            :param: project_id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/feature_flags_user_lists
        """
        return self.api.list_all(host, token, f"projects/{project_id}/feature_flags_user_lists")

    def get_single_project_feature_flag_user_list(self, host, token, project_id, feature_flag_user_list_iid):
        """
        Get a single project feature flag user list by internal id

        GitLab API Doc: https://docs.gitlab.com/ee/api/feature_flag_user_lists.html#get-a-feature-flag-user-list

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: project_id: (int) GitLab project ID
            :param: feature_flag_user_list_iid: (int/str) The name of the feature flag.
            :yield: Response object containing the response to GET GET /projects/:id/feature_flags_user_lists/:iid

        """
        return self.api.generate_get_request(host, token, f"projects/{project_id}/feature_flags_user_lists/{feature_flag_user_list_iid}")

    def create_project_feature_flag_user_list(self, host, token, project_id, name, destination_user_xids):
        """
        Creates a single project feature flag user list in a project.

        GitLab API Doc: https://docs.gitlab.com/ee/api/feature_flag_user_lists.html#create-a-feature-flag-user-list

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: project_id: (int) GitLab project ID
            :param: name: (str) The name of the feature flag user list.
            :param: user_xids: (str) A comma-separated list of external user IDs. These should be the user ids on the destination when migrating, so translation will be necessary
            :yield: Response object containing the response to POST POST /projects/:id/feature_flags_user_lists
 
        """
        endpoint = f"projects/{project_id}/feature_flags_user_lists"
        data = {'name': name, 'user_xids': destination_user_xids}   
        message = f"Creating feature flag user list {data} for project ID {project_id}"
        return self.api.generate_post_request(host, token, endpoint, json.dumps(data), description=message)

    def update_feature_flag_user_list(self, host, token, project_id, feature_flag_user_list_iid, name=None, user_xids=None):
        """
        Updates a feature flag user list.

        GitLab API Doc: https://docs.gitlab.com/ee/api/feature_flag_user_lists.html#update-a-feature-flag-user-list
            
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: project_id: (int) GitLab project ID
            :param: feature_flag_name: (str) The current name of the feature flag.
            :param: description: (str) The description of the feature flag
            :param: active: (int) The active state of the flag. Supported in GitLab 13.3 and later.
            :param: new_feature_flag_name: (str) The new name of the feature flag. Supported in GitLab 13.3 and later.
            :param: strategies: (dict) Structure containing key value pairs to be changed. Many possible required fields, see
                GL API Doc
            :yield: Response object containing the response to PUT PUT /projects/:id/feature_flags_user_lists/:iid

        """
        endpoint = f"projects/{project_id}/feature_flags_user_lists/{feature_flag_user_list_iid}"
        data = {}
        if name:
            data['name'] = name
        if user_xids:
            data['user_xids'] = user_xids
        if data:
            return self.api.generate_put_request(host, token, endpoint, json.dumps(data))
        return None
