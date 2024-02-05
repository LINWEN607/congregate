from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
from congregate.migration.meta.api_models.pypi_package_data import PyPiPackageData

class PyPiPackagesApi(GitLabApiWrapper):

    def download_pypi_group_package(self, host, token, gid, sha, file_identifier):
        """
        Download a PyPI package file from a group registry

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/pypi.html#download-a-package-file-from-a-group

            :param host: (str) GitLab host URL
            :param token: (str) Access token to GitLab instance
            :param gid: (int) GitLab group ID
            :param sha: (str) The PyPI package file's sha256 checksum
            :param file_identifier: (str) The PyPI package file's name
            :return: Response object containing the response to GET groups/:id/-/packages/pypi/files/:sha256/:file_identifier
        """
        return self.api.generate_get_request(host, token, f"groups/{gid}/-/packages/pypi/files/{sha}/{file_identifier}")
    
    def download_pypi_project_package(self, host, token, pid, sha, file_identifier):
        """
        Download a PyPI package file from a project registry

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/pypi.html#download-a-package-file-from-a-project

            :param host: (str) GitLab host URL
            :param token: (str) Access token to GitLab instance
            :param pid: (int) GitLab project ID
            :param sha: (str) The PyPI package file's sha256 checksum
            :param file_identifier: (str) The PyPI package file's name
            :return: Response object containing the response to GET projects/:id/-/packages/pypi/files/:sha256/:file_identifier
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/packages/pypi/files/{sha}/{file_identifier}")
    
    def upload_pypi_package(self, host, token, pid, package_data: PyPiPackageData):
        """
        Upload a PyPI package

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/pypi.html#upload-a-package

            :param host: (str) GitLab host URL
            :param token: (str) Access token to GitLab instance
            :param pid: (int) GitLab project ID
            :param package_data: (PyPiPackageData) Package data object
            :return: Response object containing the response to POST projects/:id/packages/pypi
        """
        return self.api.generate_post_request(host, token, f"projects/{pid}/packages/pypi", data=package_data.to_multipart_data())
    
