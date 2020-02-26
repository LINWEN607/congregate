from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.helpers.misc_utils import strip_numbers, remove_dupes

class IssuesApi(BaseClass):
    def get_all_project_issues(self, project_id, host, token):
        """
        Get a list of issues for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-project-issues

            :param: project_id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues
        """
        return api.list_all(host, token, "projects/%d/issues" % project_id)


    def get_all_group_issues(self, host, token, group_id):
        """
        Get a list of issues for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-group-issues

            :param: group_id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/issues
        """
        return api.list_all(host, token, "groups/%d/issues" % group_id)

    def get_single_project_issue(self, host, token, project_id, issue_iid):
        """
        Get a single project issue

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-group-issues

            :param: project_id: (int) GitLab project ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:id/issues/:issue_iid
        """
        return api.generate_get_request(host, token, "projects/%d/issues/%d" % (project_id, issue_iid))

    def get_project_issue_notes(self, host, token, project_id, issue_iid):
        """
        Gets a list of all notes for a single issue

        GitLab API Doc: https://docs.gitlab.com/ee/api/notes.html#list-project-issue-notes

            :param: project_id: (int) GitLab group ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues/:issue_iid/notes
        """
        return api.generate_get_request(host, token, "projects/%d/issues/%d/notes" % (project_id, issue_iid))

    def get_project_issue_awards(self, host, token, project_id, issue_iid):
        """
        Get a list of all award emoji for a specified issue

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#list-an-awardables-award-emoji

            :param: project_id: (int) GitLab group ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues/:issue_iid/award_emoji
        """
        return api.generate_get_request(host, token, "projects/%d/issues/%d/award_emoji" % (project_id, issue_iid))

    def get_project_issue_merge_requests(self, host, token, project_id, issue_iid):
        """
        Get all the merge requests that are related to the issue

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-merge-requests-related-to-issue

            :param: project_id: (int) GitLab group ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues/:issue_id/related_merge_requests
        """
        return api.generate_get_request(host, token, "projects/%d/issues/%d/related_merge_requests" % (project_id, issue_iid))

    def get_project_issue_close_by_merge_requests(self, host, token, project_id, issue_iid):
        """
        Get all the merge requests that will close issue when merged

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-merge-requests-that-will-close-issue-on-merge

            :param: project_id: (int) GitLab group ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues/:issue_iid/closed_by
        """
        return api.generate_get_request(host, token, "projects/%d/issues/%d/closed_by" % (project_id, issue_iid))

    def get_project_issue_participants(self, host, token, project_id, issue_iid):
        """
        Get all the participants of the given project issue

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#participants-on-issues

            :param: project_id: (int) GitLab group ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues/:issue_iid/participants
        """
        return api.generate_get_request(host, token, "projects/%d/issues/%d/participants" % (project_id, issue_iid))
