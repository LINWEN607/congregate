from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
import json


class IssueLinksApi(GitLabApiWrapper):
    def list_issue_links(self, host, token, project_id, issue_iid):
        """
        List all issue links for a given issue

        GitLab API Doc: https://docs.gitlab.com/ee/api/issue_links.html#list-issue-links

            :param: project_id: (int) GitLab project ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:project_id/issues/:issue_iid/links
        """
        return self.api.generate_get_request(host, token, f"projects/{project_id}/issues/{issue_iid}/links")

    def create_issue_link(self, host, token, project_id, issue_iid, target_project_id, target_issue_iid, link_type='relates_to'):
        """
        Create an issue link

        GitLab API Doc: https://docs.gitlab.com/ee/api/issue_links.html#create-an-issue-link

            :param: project_id: (int) GitLab project ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: target_project_id: (int) GitLab project ID of the target issue
            :param: target_issue_iid: (int) Internal ID of the target issue
            :param: link_type: (str) Type of relation (default is 'relates_to')
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:project_id/issues/:issue_iid/links
        """
        endpoint = f"projects/{project_id}/issues/{issue_iid}/links"
        data = {
            'target_project_id': target_project_id,
            'target_issue_iid': target_issue_iid,
            'link_type': link_type
        }
        return self.api.generate_post_request(host, token, endpoint, json.dumps(data))

    def delete_issue_link(self, host, token, project_id, issue_iid, issue_link_id):
        """
        Delete an issue link

        GitLab API Doc: https://docs.gitlab.com/ee/api/issue_links.html#delete-an-issue-link

            :param: project_id: (int) GitLab project ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: issue_link_id: (int) ID of the issue link
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to DELETE /projects/:project_id/issues/:issue_iid/links/:issue_link_id
        """
        endpoint = f"projects/{project_id}/issues/{issue_iid}/links/{issue_link_id}"
        return self.api.generate_delete_request(host, token, endpoint)

    def get_issue_link(self, host, token, project_id, issue_iid, issue_link_id):
        """
        Get a single issue link

        GitLab API Doc: https://docs.gitlab.com/ee/api/issue_links.html#get-an-issue-link

            :param: project_id: (int) GitLab project ID
            :param: issue_iid: (int) Internal ID of an issue
            :param: issue_link_id: (int) ID of the issue link
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/:project_id/issues/:issue_iid/links/:issue_link_id
        """
        endpoint = f"projects/{project_id}/issues/{issue_iid}/links/{issue_link_id}"
        return self.api.generate_get_request(host, token, endpoint)
