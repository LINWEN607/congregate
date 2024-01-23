from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
import json


class IssuesApi(GitLabApiWrapper):
    def get_all_project_issues(self, pid, host, token):
        """
        Get a list of issues for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-project-issues

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues
        """
        return self.api.list_all(host, token, f"projects/{pid}/issues")

    def get_all_group_issues(self, gid, host, token):
        """
        Get a list of issues for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-group-issues

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/issues
        """
        return self.api.list_all(host, token, f"groups/{gid}/issues")

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
        return self.api.generate_get_request(host, token, f"projects/{project_id}/issues/{issue_iid}")

    def update_issue(self, host, token, project_id, issue_iid, data):
        """
        Update a existing issue.

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#edit-issue

            :param: project_id: (int) GitLab project ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Structure containing key value pairs to be changed. Many possible required fields, see
                GL API Doc
            :yield: Response object containing the response to PUT /projects/:id/issues/:issue_iid
        """
        endpoint = f"projects/{project_id}/issues/{issue_iid}"
        return self.api.generate_put_request(host, token, endpoint, json.dumps(data))

    def create_issue(self, host, token, project_id, title=None, description=None):
        """
        Creates a single issue in a project.

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#new-issue
        """
        endpoint = f"projects/{project_id}/issues"
        data = {'title': title, 'description': description}
        message = f"Creating PM sign off issue: {title} at: {endpoint}"
        return self.api.generate_post_request(host, token, endpoint, json.dumps(data), description=message)

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
        return self.api.list_all(host, token, f"projects/{pid}/issues/{iid}/notes")

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
        return self.api.generate_get_request(
            host,
            token,
            f"projects/{project_id}/issues/{issue_iid}/notes/{note_id}/award_emoji"
        )

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
        return self.api.generate_post_request(
            host,
            token,
            f"projects/{project_id}/issues/{issue_iid}/notes/{note_id}/award_emoji?name={name}",
            None
        )

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
        return self.api.generate_get_request(host, token, f"projects/{project_id}/issues/{issue_iid}/award_emoji")

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
        return self.api.generate_post_request(
            host,
            token,
            f"projects/{project_id}/snippets/{issue_iid}/award_emoji?name={name}",
            None
        )

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
        return self.api.generate_get_request(host, token, f"projects/{project_id}/issues/{issue_iid}/related_merge_requests")

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
        return self.api.generate_get_request(host, token, f"projects/{project_id}/issues/{issue_iid}/closed_by")

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
        return self.api.generate_get_request(host, token, f"projects/{project_id}/issues/{issue_iid}/participants")
