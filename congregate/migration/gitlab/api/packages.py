from congregate.migration.gitlab.api.base_api import GitLabApiWrapper

class PackagesApi(GitLabApiWrapper):

<<<<<<< HEAD
    def get_project_packages(self, host, token, project):
=======
    def get_project_packages(self, host, token, project):
>>>>>>> 138d6a716b3c61745ec9466277b5bdd8898b2bc3
        """
        List packages within a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages.html#within-a-project

            :param: project: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/packages
        """
        return self.api.list_all(host, token, f"projects/{project}/packages")

<<<<<<< HEAD
    def get_group_packages(self, host, token, group):
=======
    def get_group_packages(self, host, token, group):
>>>>>>> 138d6a716b3c61745ec9466277b5bdd8898b2bc3
        """
        List packages within a group

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages.html#within-a-group

            :param: group: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/packages
        """
        return self.api.list_all(host, token, f"groups/{group}/packages")

    def get_single_project_package(self, host, token, project, package):
        """
        Get a single project package

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages.html#get-a-project-package

            :param: project: (int) GitLab project ID
            :param: package: (int) GitLab package ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/:id/packages/:package_id
        """
        return self.api.generate_get_request(host, token, f"projects/{project}/packages/{package}")

    def get_package_files(self, host, token, project, package):
        """
        Get a list of package files of a single package

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages.html#list-package-files

            :param: project: (int) GitLab project ID
            :param: package: (int) GitLab package ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/packages/:package_id/package_files
        """
        return self.api.list_all(host, token, f"projects/{project}/packages/{package}/package_files")

    def delete_project_package(self, host, token, project, package):
        """
        Deletes a project package

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages.html#delete-a-project-package

            :param: project: (int) GitLab project ID
            :param: package: (int) GitLab package ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 204 (No Content) or 404 (not found) from DELETE /projects/:id/packages/:package_id
        """
        return self.api.generate_delete_request(host, token, f"projects/{project}/packages/{package}")

    def delete_package_file(self, host, token, project, package, package_file):
        """
        Delete a package file

        GitLab API Doc: https://docs.gitlab.com/ee/api/packages.html#delete-a-package-file

            :param: project: (int) GitLab project ID
            :param: package: (int) GitLab package ID
            :param: package_file: (int) GitLab package file ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 204 (No Content) or 404 (not found) from DELETE /projects/:id/packages/:package_id/package_files/:package_file_id
        """
        return self.api.generate_delete_request(host, token, f"projects/{project}/packages/{package}/package_files/{package_file}")