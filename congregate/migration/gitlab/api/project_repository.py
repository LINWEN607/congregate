from urllib.parse import quote_plus
from congregate.helpers import api
import json

class ProjectRepositoryApi():
    def get_all_project_repository_tree(self, id, host, token):
        """
        Get a list of repository files and directories in a project

        https://docs.gitlab.com/ee/api/repositories.html#list-repository-tree

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/repository/tree
        """
        return api.list_all(host, token, "projects/%d/repository/tree" % id)

    def get_all_project_repository_contributors(self, id, host, token):
        """
        Get repository contributors list

        https://docs.gitlab.com/ee/api/repositories.html#contributors

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/repository/contributors
        """
        return api.list_all(host, token, "projects/%d/repository/contributors" % id)

    def get_all_project_repository_branches(self, pid, host, token, query_params=""):
        """
        Get a list of repository branches from a project

        https://docs.gitlab.com/ee/api/branches.html#list-repository-branches

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: query_params: (str) Query parameters
            :yield: Generator returning JSON of each result from GET /projects/:id/repository/branches
        """
        return api.list_all(host, token, "projects/{0}/repository/branches{1}".format(pid, query_params))

    def get_single_project_repository_branch(self, host, token, pid, branch_name):
        """
        Get a single project repository branch

        https://docs.gitlab.com/ee/api/branches.html#get-single-repository-branch

            :param: pid: (int) GitLab project ID
            :param: branch_name: (str) Branch name
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:id/repository/branches/:branch
        """
        return api.generate_get_request(host, token, "projects/%d/repository/branches/%s" % (pid, quote_plus(branch_name)))

    def get_all_project_repository_tags(self, id, host, token):
        """
        Get a list of repository tags from a project

        https://docs.gitlab.com/ee/api/tags.html#list-project-repository-tags

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/repository/tags
        """
        return api.list_all(host, token, "projects/%d/repository/tags" % id)

    def get_all_project_repository_commits(self, pid, host, token, query_params=""):
        """
        Get a list of repository commits in a project

        https://docs.gitlab.com/ee/api/commits.html#list-repository-commits

            :param: pid: (int) GitLab project ID
            :param: query_params: (str) Query parameters
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/repository/commits
        """
        return api.list_all(host, token, "projects/{0}/repository/commits{1}".format(pid, query_params))

    def get_single_project_repository_commit(self, host, token, id, sha):
        """
        Get a specific commit identified by the commit hash or name of a branch or tag

        https://docs.gitlab.com/ee/api/commits.html#get-a-single-commit

            :param: id: (int) GitLab project ID
            :param: sha: (str) The commit hash or name of a repository branch or tag
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response GET /projects/:id/repository/commits/:sha
        """
        return api.generate_get_request(host, token, "projects/%d/repository/commits/%s" % (id, sha))

    def get_project_repository_commit_diff(self, pid, sha, host, token):
        """
        Get the diff of a commit in a project

        https://docs.gitlab.com/ee/api/commits.html#get-the-diff-of-a-commit

            :param: pid: (int) GitLab project ID
            :param: sha: (int) Commit SHA
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/repository/commits/:sha/diff
        """
        return api.list_all(host, token, "projects/{0}/repository/commits/{1}/diff".format(pid, sha))

    def get_project_repository_commit_comments(self, pid, sha, host, token):
        """
        Get the comments of a commit in a project

        https://docs.gitlab.com/ee/api/commits.html#get-the-comments-of-a-commit

            :param: pid: (int) GitLab project ID
            :param: sha: (int) Commit SHA
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/repository/commits/:sha/comments
        """
        return api.list_all(host, token, "projects/{0}/repository/commits/{1}/comments".format(pid, sha))

    def get_project_repository_commit_refs(self, host, token, pid, sha, query_params=""):
        """
        Get all references (from branches or tags) a commit is pushed to

        https://docs.gitlab.com/ee/api/commits.html#get-references-a-commit-is-pushed-to

            :param: pid: (int) GitLab project ID
            :param: sha: (int) Commit SHA
            :param: query_params: (str) Query parameters
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/repository/commits/:sha/refs
        """
        return api.list_all(host, token, "projects/%d/repository/commits/%s/refs%s" % (pid, sha, query_params))

    def get_project_repository_commit_merge_requests(self, pid, sha, host, token):
        """
        Get a list of Merge Requests related to the specified commit

        https://docs.gitlab.com/ee/api/commits.html#list-merge-requests-associated-with-a-commit

            :param: pid: (int) GitLab project ID
            :param: sha: (int) Commit SHA
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/repository/commits/:sha/merge_requests
        """
        return api.list_all(host, token, "projects/{0}/repository/commits/{1}/merge_requests".format(pid, sha))

    def get_project_repository_commit_statuses(self, pid, sha, host, token):
        """
        List the statuses of a commit in a project

        https://docs.gitlab.com/ee/api/commits.html#list-the-statuses-of-a-commit

            :param: pid: (int) GitLab project ID
            :param: sha: (int) Commit SHA
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/repository/commits/:sha/statuses
        """
        return api.list_all(host, token, "projects/{0}/repository/commits/{1}/statuses".format(pid, sha))


    def create_repo_file(self, host, token, pid, filepath, data, message=None):
        """
        Create new file in repository

        https://docs.gitlab.com/ee/api/repository_files.html#create-new-file-in-repository
            :param: pid: (int) GitLab project ID
            :param: filepath (str) the file path with filename 
            :param: data(str) the data including branch, content and commit message
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
        """
        if not message:
            message = f"Adding a {filepath} for project {pid} with {data}"
        return api.generate_post_request(host, token, f"projects/{pid}/repository/files/{filepath}", json.dumps(data), description=message)
    
    def get_single_repo_file(self, host, token, pid, filepath, branch):
        """
        Get a single repository file via the API
        
        https://docs.gitlab.com/ee/api/repository_files.html#get-file-from-repository
            :param: pid: (int) GitLab project ID
            :param: filepath (str) the unencoded file path with filename
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
        """
        return api.generate_get_request(host, token, f"projects/{pid}/repository/files/{quote_plus(filepath)}?ref={branch}")

    def put_single_repo_file(self, host, token, pid, filepath, put_file_data):
        """
        Update a single repository file via the API
        
        https://docs.gitlab.com/ee/api/repository_files.html#update-existing-file-in-repository
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
        return api.generate_put_request(host, token, f"projects/{pid}/repository/files/{quote_plus(filepath)}", json.dumps(put_file_data))
