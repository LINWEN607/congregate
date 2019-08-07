from congregate.helpers import api
import json

class GroupsApi():
    def get_group(self, id, host, token):
        """
        Get all details of a group
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#details-of-a-group

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /groups/:id

        """
        return api.generate_get_request(host, token, "groups/%d" % id)

    def search_for_group(self, name, host, token):
        """
        Get all groups that match your string in their name or path.
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#search-for-group

            :param: name: (string) Group name or url encoded full path to a group
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups?search=:name

        """
        return api.list_all(host, token, "groups?search=%s" % name)

    def create_group(self, host, token, data):
        """
        Creates a new project group
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#new-group

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the various data requried for creating a group. Refer to the link above for specific examples
            :return: Response object containing the response to POST /groups

        """
        return api.generate_post_request(host, token, "groups", json.dumps(data))

    def add_member_to_group(self, id, host, token, member):
        """
        Adds a member to a group or project
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#add-a-member-to-a-group-or-project

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: member: (dict) Object containing the member data. Refer to the link above for specific examples
            :return: Response object containing the response to POST /groups/:id/members

        """
        return api.generate_post_request(host, token, "groups/%d/members" % id, json.dumps(member))

    def get_all_groups(self, host, token):
        """
        Get a list of visible groups for the authenticated user
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-groups

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups

        """
        return api.list_all(host, token, "groups")

    def get_all_group_members(self, id, host, token):
        """
        https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /groups/:id/members

        """
        return api.list_all(host, token, "groups/%d/members" % id)

    def get_all_subgroups(self, id, host, token):
        """
        Get a list of visible direct subgroups in this group
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-a-groups-subgroups

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /groups/:id/subgroups

        """
        return api.list_all(host, token, "groups/%d/subgroups" % id)

    def delete_group(self, id, host, token):
        """
        Removes group with all projects inside
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#remove-group

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 202 (accepted) or 404 (Group not found) from DELETE /groups/:id

        """
        return api.generate_delete_request(host, token, "groups/%d" % id)