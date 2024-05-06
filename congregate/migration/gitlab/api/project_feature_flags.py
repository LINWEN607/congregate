from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
import json


class ProjectFeatureFlagsApi(GitLabApiWrapper):
    def get_all_project_feature_flags(self, host, token, project_id):
        """
        Get a list of feature flags for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/feature_flags.html#list-feature-flags-for-a-project

            :param: project_id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/feature_flags
        """
        return self.api.list_all(host, token, f"projects/{project_id}/feature_flags")

    def get_single_project_feature_flag(self, host, token, project_id, feature_flag_name):
        """
        Get a single project feature flag by name

        GitLab API Doc: https://docs.gitlab.com/ee/api/feature_flags.html#get-a-single-feature-flag

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: project_id: (int) GitLab project ID
            :param: feature_flag_name: (str) The name of the feature flag.
            :yield: Response object containing the response to GET /projects/:id/issues/:issue_iid
        """
        return self.api.generate_get_request(host, token, f"projects/{project_id}/feature_flags/{feature_flag_name}")

    def create_feature_flag(self, host, token, project_id, name, version="new_version_flag", description=None, active=None, strategies=None):
        """
        Creates a single feature flag in a project.

        GitLab API Doc: https://docs.gitlab.com/ee/api/feature_flags.html#create-a-feature-flag

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: project_id: (int) GitLab project ID
            :param: name: (str) The name of the feature flag.
            :param: version: (str) **Deprecated** The version of the feature flag. Must be new_version_flag. Omit to create a Legacy feature flag.
            :param: description: (str) The description of the feature flag
            :param: active: (int) The active state of the flag. Supported in GitLab 13.3 and later.
            :param: strategies: (dict) Structure containing key value pairs to be changed. Many possible required fields, see
                GL API Doc
            :yield: Response object containing the response to POST /projects/:project_id/feature_flags/    
        """
        endpoint = f"projects/{project_id}/feature_flags"
        data = {'name': name, 'version': version} 
        if description:
            data['description'] = description
        if active:
            data['active'] = active
        if strategies:
            data['strategies'] = strategies        
        message = f"Creating feature flag {data} for project ID {project_id}"
        return self.api.generate_post_request(host, token, endpoint, json.dumps(data), description=message)

    def update_feature_flag(self, host, token, project_id, current_feature_flag_name, description=None, active=None, new_feature_flag_name=None, strategies=None):
        """
        Updates a feature flag.

        GitLab API Doc: https://docs.gitlab.com/ee/api/feature_flags.html#update-a-feature-flag
            
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: project_id: (int) GitLab project ID
            :param: feature_flag_name: (str) The current name of the feature flag.
            :param: description: (str) The description of the feature flag
            :param: active: (int) The active state of the flag. Supported in GitLab 13.3 and later.
            :param: new_feature_flag_name: (str) The new name of the feature flag. Supported in GitLab 13.3 and later.
            :param: strategies: (dict) Structure containing key value pairs to be changed. Many possible required fields, see
                GL API Doc
            :yield: Response object containing the response to PUT /projects/:project_id/feature_flags/:current_feature_flag_name
        """
        endpoint = f"projects/{project_id}/feature_flags/{current_feature_flag_name}"
        data = {}
        if new_feature_flag_name:
            data['name'] = new_feature_flag_name
        if description:
            data['description'] = description
        if active:
            data['active'] = active
        if strategies:
            data['strategies'] = strategies
        if data:
            return self.api.generate_put_request(host, token, endpoint, json.dumps(data))
        return None
