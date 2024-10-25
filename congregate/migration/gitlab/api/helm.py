from copy import deepcopy as copy
from urllib.parse import quote_plus
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
from congregate.migration.meta.api_models.helm_package_data import HelmPackageData

class HelmPackagesApi(GitLabApiWrapper):
    
    def download_helm_project_package(self, host, token, pid, package_name, file_name):
        """
        Download a Helm package file

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/npm.html#download-a-package

            :param host: (str) GitLab host URL.
            :param token: (str) Access token to GitLab instance.
            :param pid: (int) GitLab project ID.
            :param package_name: (str) The name of the package.
            :param file_name: (str) The name of the package file.
            :return: Response object containing the response to GET projects/:id/packages/npm/:package_name/-/:file_name
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/packages/npm/{package_name}/-/{file_name}")
    
    def download_helm_package_metadata(self, host, token, pid, package_name):
        """
        Get a Helm package file metadata

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/npm.html#metadata

            :param host: (str) GitLab host URL.
            :param token: (str) Access token to GitLab instance.
            :param pid: (int) GitLab project ID.
            :param package_name: (str) The name of the package.
            :return: Response object containing the response to GET projects/:id/packages/npm/:package_name
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/packages/npm/{package_name}")
    
    def upload_helm_package(self, host, token, pid, channel, json_data, package_data: HelmPackageData):
        """
        Upload a Helm package file

        GitLab API Doc: https://docs.gitlab.com/ee/user/packages/helm_repository/#publish-a-package

            :param host: (str) GitLab host URL
            :param token: (str) Access token to GitLab instance
            :param pid: (int) GitLab project ID
            :param package_data: (HelmPackageData) Package data object
            :return: Response object containing the response to PUT projects/:id/packages/helm/api/:channel/charts
        """
        headers = {
            'Private-Token': token,
            'Content-Type': 'application/json'
        }
        filtered_message = copy(package_data.to_dict())
        filtered_message.pop('content', None)

        message = f"Uploading to Helm registry with payload {filtered_message}"
        
        return self.api.generate_put_request(host, token, f"projects/{pid}/packages/helm/api/{channel}/@{quote_plus(package_data.name).lstrip('@')}", data=json_data, headers=headers, description=message)
