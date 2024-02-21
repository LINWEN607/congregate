import json
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
from congregate.migration.meta.api_models.npm_package_data import NpmPackageData

class NpmPackagesApi(GitLabApiWrapper):
    
    def download_npm_project_package(self, host, token, pid, package_name, file_name):
        """
        Download a NPM package file

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/npm.html#download-a-package

            :param host: (str) GitLab host URL.
            :param token: (str) Access token to GitLab instance.
            :param pid: (int) GitLab project ID.
            :param package_name: (str) The name of the package.
            :param file_name: (str) The name of the package file.
            :return: Response object containing the response to GET projects/:id/packages/npm/:package_name/-/:file_name
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/packages/npm/{package_name}/-/{file_name}")
    
    def download_npm_package_metadata(self, host, token, pid, package_name):
        """
        Get a NPM package file metadata

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/npm.html#metadata

            :param host: (str) GitLab host URL.
            :param token: (str) Access token to GitLab instance.
            :param pid: (int) GitLab project ID.
            :param package_name: (str) The name of the package.
            :return: Response object containing the response to GET projects/:id/packages/npm/:package_name
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/packages/npm/{package_name}")
    
    def upload_npm_package(self, host, token, pid, json_data, package_data: NpmPackageData):
        """
        Upload a NPM package file

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/npm.html#upload-a-package-file

            :param host: (str) GitLab host URL
            :param token: (str) Access token to GitLab instance
            :param pid: (int) GitLab project ID
            :param package_data: (NpmPackageData) Package data object
            :return: Response object containing the response to PUT projects/:id/packages/npm/:package_name
        """
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        return self.api.generate_put_request(host, token, f"projects/{pid}/packages/npm/{package_data.name}", data=json_data, headers=headers)
    
