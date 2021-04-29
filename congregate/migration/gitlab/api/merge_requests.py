from congregate.migration.gitlab.api.base_api import GitLabApiWrapper


class MergeRequestsApi(GitLabApiWrapper):
    def get_all_project_merge_requests(self, pid, host, token):
        """
        Get all merge requests for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_requests.html#list-project-merge-requests

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/merge_requests
        """
        return self.api.list_all(host, token, "projects/{}/merge_requests".format(pid))

    def get_all_group_merge_requests(self, gid, host, token):
        """
        Get all merge requests for the given group

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_requests.html#list-group-merge-requests

            :param: gid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/merge_requests
        """
        return self.api.list_all(host, token, "groups/{}/merge_requests".format(gid))

    def get_single_project_merge_requests(self, host, token, project_id, mr_iid):
        """
        Shows information about a single merge request

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_requests.html#get-single-mr

            :param: project_id: (int) GitLab project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:id/merge_requests/:merge_request_iid
        """
        return self.api.generate_get_request(host, token, "projects/%d/merge_requests/%d" % (project_id, mr_iid))

    def get_merge_request_participants(self, host, token, project_id, mr_iid):
        """
        Get a list of merge request participants

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_requests.html#get-single-mr-participants

            :param: project_id: (int) GitLab Project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/merge_requests/:merge_request_iid/participants
        """
        return self.api.list_all(host, token, "projects/%d/merge_requests/%d/participants" % (project_id, mr_iid))

    def get_merge_request_notes(self, host, token, project_id, mr_iid):
        """
        Gets a list of all notes for a single merge request

        GitLab API Doc: https://docs.gitlab.com/ee/api/notes.html#list-all-merge-request-notes

            :param: project_id: (int) GitLab Project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/merge_requests/:merge_request_iid/notes
        """
        return self.api.list_all(host, token, "projects/%d/merge_requests/%d/notes" % (project_id, mr_iid))

    def get_merge_request_awards(self, host, token, project_id, mr_iid):
        """
        Get a list of all award emoji for a specified project

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#list-an-awardables-award-emoji

            :param: project_id: (int) GitLab Project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/merge_requests/:merge_request_iid/award_emoji
        """
        return self.api.list_all(host, token, "projects/%d/merge_requests/%d/award_emoji" % (project_id, mr_iid))

    def create_merge_request_award(self, host, token, project_id, mr_iid, name):
        """
        Create an award emoji on the specified project merge request

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#award-a-new-emoji

            :param: project_id: (int) GitLab project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: name: (int) Name of the award
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/merge_requests/:merge_request_iid/award_emoji
        """
        return self.api.generate_post_request(host, token, "projects/%d/merge_requests/%d/award_emoji?name=%s" % (project_id, mr_iid, name), None)

    def get_merge_request_note_awards(self, host, token, project_id, mr_iid, note_id):
        """
        Get all award emoji for a merge request note

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#get-an-award-emoji-for-a-comment

            :param: project_id: (int) GitLab group ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: note_id: (int) Note ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/merge_requests/:mr_iid/notes/:note_id/award_emoji
        """
        return self.api.generate_get_request(host, token, "projects/%d/merge_requests/%d/notes/%d/award_emoji" % (project_id, mr_iid, note_id))

    def create_merge_request_note_award(self, host, token, project_id, mr_iid, note_id, name):
        """
        Create an award emoji on the specified project merge request note

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#award-a-new-emoji-on-a-comment

            :param: project_id: (int) GitLab project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: note_id: (int) Note ID
            :param: name: (int) Name of the award
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/merge_requests/:mr_iid/notes/:note_id/award_emoji
        """
        return self.api.generate_post_request(host, token, "projects/%d/merge_requests/%d/notes/%d/award_emoji?name=%s" % (project_id, mr_iid, note_id, name), None)

    def get_merge_request_changes(self, host, token, project_id, mr_iid):
        """
        Shows information about the merge request including its files and changes

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_requests.html#get-single-mr-changes

            :param: project_id: (int) GitLab Project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/merge_requests/:merge_request_iid/changes
        """
        return self.api.list_all(host, token, "projects/%d/merge_requests/%d/changes" % (project_id, mr_iid))

    def get_merge_request_commits(self, host, token, project_id, mr_iid):
        """
        Get a list of merge request commits

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_requests.html#get-single-mr-commits

            :param: project_id: (int) GitLab Project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/merge_requests/:merge_request_iid/commits
        """
        return self.api.list_all(host, token, "projects/%d/merge_requests/%d/commits" % (project_id, mr_iid))

    def get_merge_request_diff_versions(self, host, token, project_id, mr_iid):
        """
        Get a list of merge request diff versions

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_requests.html#get-mr-diff-versions

            :param: project_id: (int) GitLab Project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/merge_requests/:merge_request_iid/versions
        """
        return self.api.list_all(host, token, "projects/%d/merge_requests/%d/versions" % (project_id, mr_iid))

    def get_merge_request_pipelines(self, host, token, project_id, mr_iid):
        """
        Get a list of merge request pipelines

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_requests.html#list-mr-pipelines

            :param: project_id: (int) GitLab Project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/merge_requests/:merge_request_iid/pipelines
        """
        return self.api.list_all(host, token, "projects/%d/merge_requests/%d/pipelines" % (project_id, mr_iid))

    def get_merge_request_approvals(self, host, token, project_id, mr_iid):
        """
        Get the approval status of a merge request

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_request_approvals.html#get-configuration-1

            :param: project_id: (int) GitLab Project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:id/merge_requests/:merge_request_iid/approvals
        """
        return self.api.list_all(host, token, "projects/%d/merge_requests/%d/approvals" % (project_id, mr_iid))

    def get_merge_request_approval_rules(self, host, token, project_id, mr_iid):
        """
        Get the approval rules of a merge request

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_request_approvals.html#get-merge-request-level-rules

            :param: project_id: (int) GitLab Project ID
            :param: mr_iid: (int) Internal ID of the merge request
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/merge_requests/:merge_request_iid/approval_rules
        """
        return self.api.list_all(host, token, "projects/%d/merge_requests/%d/approval_rules" % (project_id, mr_iid))
