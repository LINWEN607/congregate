from urllib.parse import quote_plus
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
from congregate.migration.meta.api_models.npm_package_data import NpmPackageData

class MavenPackagesApi(GitLabApiWrapper):
    
    def download_maven_project_package(self, host, token, pid, path, file_name):
        """
        Download a Maven project package file

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/maven.html#download-a-package-file-at-the-project-level

            :param host: (str) GitLab host URL
            :param token: (str) Access token to GitLab instance
            :param pid: (int) GitLab project ID
            :param path: (str) The Maven package path, in the format <groupId>/<artifactId>/<version>. Replace any . in the groupId with /.
            :param file_name: (str) The name of the Maven package file.
            :return: Response object containing the response to GET projects/:id/packages/maven/*path/:file_name
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/packages/maven/{path}/{file_name}")

    def download_maven_instance_package(self, host, token, path, file_name):
        """
        Download a Maven instance package file

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/maven.html#download-a-package-file-at-the-instance-level

            :param host: (str) GitLab host URL
            :param token: (str) Access token to GitLab instance
            :param path: (str) The Maven package path, in the format <groupId>/<artifactId>/<version>. Replace any . in the groupId with /.
            :param file_name: (str) The name of the Maven package file.
            :return: Response object containing the response to GET packages/maven/*path/:file_name
        """
        return self.api.generate_get_request(host, token, f"packages/maven/{path}/{file_name}")

    def download_maven_group_package(self, host, token, pid, path, file_name):
        """
        Download a Maven group package file

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/maven.html#download-a-package-file-at-the-group-level

            :param host: (str) GitLab host URL
            :param token: (str) Access token to GitLab instance
            :param pid: (int) GitLab group ID
            :param path: (str) The Maven package path, in the format <groupId>/<artifactId>/<version>. Replace any . in the groupId with /.
            :param file_name: (str) The name of the Maven package file.
            :return: Response object containing the response to GET groups/:id/-/packages/maven/*path/:file_name
        """
        return self.api.generate_get_request(host, token, f"groups/{pid}/-/packages/maven/{path}/{file_name}")
    
    def upload_maven_package(self, host, token, pid, path, file, file_name):
        """
        Upload a Maven package file

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages/maven.html#upload-a-package-file

            :param host: (str) GitLab host URL
            :param token: (str) Access token to GitLab instance
            :param pid: (int) GitLab project ID
            :param path: (str) The Maven package path, in the format <groupId>/<artifactId>/<version>. Replace any . in the groupId with /.
            :param file_name: (str) The name of the Maven package file.
            :return: Response object containing the response to PUT projects/:id/packages/maven/*path/:file_name
        """
        headers = {
            'Private-Token': token,
            'Content-Type': 'application/octet-stream'
        }
        
        return self.api.generate_put_request(host, token, f"projects/{pid}/packages/maven/{path}/{file_name}", data=file, headers=headers)
