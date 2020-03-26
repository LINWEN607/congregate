from congregate.helpers.base_class import BaseClass
from congregate.helpers import api


class IssuesApi(BaseClass):
    def get_all_project_issues(self, pid, host, token):
        """
        Get a list of issues for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-project-issues

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues
        """
        return api.list_all(host, token, "projects/{}/issues".format(pid))

    def get_all_group_issues(self, gid, host, token):
        """
        Get a list of issues for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-group-issues

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/issues
        """
        return api.list_all(host, token, "groups/{}/issues".format(gid))

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

    def get_all_project_issue_notes(self, pid, iid, host, token):
        """
        Gets a list of all notes for a single issue

        GitLab API Doc: https://docs.gitlab.com/ee/api/notes.html#list-project-issue-notes

            :param: pid: (int) GitLab group ID
            :param: iid: (int) Internal ID of an issue
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues/:issue_iid/notes
        """
        return api.list_all(host, token, "projects/{0}/issues/{1}/notes".format(pid, iid))

    def get_project_issue_note_awards(self, host, token, project_id, issue_iid, note_id):
        """
        Get all award emoji for an issue note

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#get-an-award-emoji-for-a-comment

            :param: project_id: (int) GitLab group ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: note_id: (int) Note ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues/:issue_iid/notes/:note_id/award_emoji
        """
        return api.generate_get_request(host, token, "projects/%d/issues/%d/notes/%d/award_emoji" % (project_id, issue_iid, note_id))

    def create_project_issue_note_award(self, host, token, project_id, issue_iid, note_id, name):
        """
        Create an award emoji on the specified project issue note

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#award-a-new-emoji-on-a-comment

            :param: project_id: (int) GitLab project ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: note_id: (int) Note ID
            :param: name: (int) Name of the award
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/issues/:issue_iid/notes/:note_id/award_emoji
        """
        return api.generate_post_request(host, token, "projects/%d/issues/%d/notes/%d/award_emoji?name=%s" % (project_id, issue_iid, note_id, name), None)

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

    def create_project_issue_award(self, host, token, project_id, issue_iid, name):
        """
        Create an award emoji on the specified project issue

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#award-a-new-emoji

            :param: project_id: (int) GitLab project ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: name: (int) Name of the award
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/snippets/:issue_iid/award_emoji
        """
        return api.generate_post_request(host, token, "projects/%d/snippets/%d/award_emoji?name=%s" % (project_id, issue_iid, name), None)

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
