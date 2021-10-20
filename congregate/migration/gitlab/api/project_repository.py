import json
from urllib.parse import quote_plus
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper


class ProjectRepositoryApi(GitLabApiWrapper):
    def get_all_project_repository_tree(self, pid, host, token):
        """
        Get a list of repository files and directories in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/repositories.html#list-repository-tree

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/repository/tree
        """
        return self.api.list_all(host, token, f"projects/{pid}/repository/tree")

    def get_all_project_repository_contributors(self, pid, host, token):
        """
        Get repository contributors list

        GitLab API Doc: https://docs.gitlab.com/ee/api/repositories.html#contributors

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/repository/contributors
        """
        return self.api.list_all(host, token, f"projects/{pid}/repository/contributors")

    def get_all_project_repository_branches(self, pid, host, token, query_params=""):
        """
        Get a list of repository branches from a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/branches.html#list-repository-branches

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: query_params: (str) Query parameters
            :yield: Generator returning JSON of each result from GET /projects/:id/repository/branches
        """
        return self.api.list_all(host, token, f"projects/{pid}/repository/branches{query_params}")

    def get_single_project_repository_branch(self, host, token, pid, branch_name):
        """
        Get a single project repository branch

        GitLab API Doc: https://docs.gitlab.com/ee/api/branches.html#get-single-repository-branch

            :param: pid: (int) GitLab project ID
            :param: branch_name: (str) Branch name
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:pid/repository/branches/:branch
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/repository/branches/{quote_plus(branch_name)}")

    def get_all_project_repository_tags(self, pid, host, token):
        """
        Get a list of repository tags from a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/tags.html#list-project-repository-tags

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/repository/tags
        """
        return self.api.list_all(host, token, f"projects/{pid}/repository/tags")

    def get_all_project_repository_commits(self, pid, host, token, query_params=""):
        """
        Get a list of repository commits in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/commits.html#list-repository-commits

            :param: pid: (int) GitLab project ID
            :param: query_params: (str) Query parameters
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/repository/commits
        """
        return self.api.list_all(host, token, f"projects/{pid}/repository/commits{query_params}")

    def get_single_project_repository_commit(self, host, token, pid, sha):
        """
        Get a specific commit identified by the commit hash or name of a branch or tag

        GitLab API Doc: https://docs.gitlab.com/ee/api/commits.html#get-a-single-commit

            :param: pid: (int) GitLab project ID
            :param: sha: (str) The commit hash or name of a repository branch or tag
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response GET /projects/:pid/repository/commits/:sha
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/repository/commits/{sha}")

    def get_project_repository_commit_diff(self, pid, sha, host, token):
        """
        Get the diff of a commit in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/commits.html#get-the-diff-of-a-commit

            :param: pid: (int) GitLab project ID
            :param: sha: (int) Commit SHA
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/repository/commits/:sha/diff
        """
        return self.api.list_all(host, token, f"projects/{pid}/repository/commits/{sha}/diff")

    def get_project_repository_commit_comments(self, pid, sha, host, token):
        """
        Get the comments of a commit in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/commits.html#get-the-comments-of-a-commit

            :param: pid: (int) GitLab project ID
            :param: sha: (int) Commit SHA
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/repository/commits/:sha/comments
        """
        return self.api.list_all(host, token, f"projects/{pid}/repository/commits/{sha}/comments")

    def get_project_repository_commit_refs(self, host, token, pid, sha, query_params=""):
        """
        Get all references (from branches or tags) a commit is pushed to

        GitLab API Doc: https://docs.gitlab.com/ee/api/commits.html#get-references-a-commit-is-pushed-to

            :param: pid: (int) GitLab project ID
            :param: sha: (int) Commit SHA
            :param: query_params: (str) Query parameters
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/repository/commits/:sha/refs
        """
        return self.api.list_all(host, token, f"projects/{pid}/repository/commits/{sha}/refs{query_params}")

    def get_project_repository_commit_merge_requests(self, pid, sha, host, token):
        """
        Get a list of Merge Requests related to the specified commit

        GitLab API Doc: https://docs.gitlab.com/ee/api/commits.html#list-merge-requests-associated-with-a-commit

            :param: pid: (int) GitLab project ID
            :param: sha: (int) Commit SHA
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/repository/commits/:sha/merge_requests
        """
        return self.api.list_all(host, token, f"projects/{pid}/repository/commits/{sha}/merge_requests")

    def get_project_repository_commit_statuses(self, pid, sha, host, token):
        """
        List the statuses of a commit in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/commits.html#list-the-statuses-of-a-commit

            :param: pid: (int) GitLab project ID
            :param: sha: (int) Commit SHA
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/repository/commits/:sha/statuses
        """
        return self.api.list_all(host, token, f"projects/{pid}/repository/commits/{sha}/statuses")

    def create_repo_file(self, host, token, pid, filepath, data, message=None):
        """
        Create new file in repository

        GitLab API Doc: https://docs.gitlab.com/ee/api/repository_files.html#create-new-file-in-repository

            :param: pid: (int) GitLab project ID
            :param: filepath (str) the file path with filename 
            :param: data(str) the data including branch, content and commit message
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
        """
        if not message:
            message = f"Adding a {filepath} for project {pid} with {data}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/repository/files/{filepath}", json.dumps(data), description=message)

    def get_single_repo_file(self, host, token, pid, filepath, branch):
        """
        Get a single repository file via the API

        GitLab API Doc: https://docs.gitlab.com/ee/api/repository_files.html#get-file-from-repository

            :param: pid: (int) GitLab project ID
            :param: filepath (str) the unencoded file path with filename
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/repository/files/{quote_plus(filepath)}?ref={branch}")

    def put_single_repo_file(self, host, token, pid, filepath, put_file_data):
        """
        Update a single repository file via the API

        GitLab API Doc: https://docs.gitlab.com/ee/api/repository_files.html#update-existing-file-in-repository

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: pid: (int) GitLab project ID
            :param: filepath (str) the unencoded file path with filename
            :param: put_file_data (dict) of the form 
                {
                    "branch": "branch_name",
                    "content": "base64 or text content",
                    "encoding": "base64 or text depending on content format",
                    "commit_message": "some commit message"
                }
        """
        return self.api.generate_put_request(host, token, f"projects/{pid}/repository/files/{quote_plus(filepath)}", json.dumps(put_file_data))

    def create_commit_with_files_and_actions(self, host, token, pid, data=None, message=None):
        """
        Create a commit by posting a JSON payload

        GitLab API Doc: https://docs.gitlab.com/ee/api/commits.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the necessary data for the added cluster
            :return: Response object containing the response to POST /projects/:id/repository/commits

        """
        if not message:
            message = f"Creating project {pid} commit with payload {data}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/repository/commits", json.dumps(data), description=message)
