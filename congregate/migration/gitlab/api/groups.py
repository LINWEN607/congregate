import json

from urllib import quote_plus
from congregate.helpers import api


class GroupsApi():
    def get_group(self, gid, host, token):
        """
        Get all details of a group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#details-of-a-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /groups/:id
        """
        return api.generate_get_request(host, token, "groups/{}".format(gid))

    def get_group_by_full_path(self, full_path, host, token):
        """
        Get all details of a group matching the full path

            :param: full_path: (string) URL encoded full path to a group
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/<full_path>
        """
        return api.generate_get_request(host, token, "groups/{}".format(quote_plus(full_path)))

    def get_namespace_by_full_path(self, full_path, host, token):
        """
        Get all details of a namespace matching the full path

            :param: full_path: (string) URL encoded full path to a group
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /namespaces/<full_path>
        """
        return api.generate_get_request(host, token, "namespaces/{}".format(quote_plus(full_path)))

    def search_for_group(self, name, host, token):
        """
        Get all groups that match your string in their name or path

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#search-for-group

            :param: name: (string) Group name or path
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

    def update_member_access_level(self, host, token, gid, uid, level):
        return api.generate_put_request(host, token, "groups/{0}/members/{1}?access_level={2}".format(gid, uid, level), data=None)

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
            :return: Response object containing a 202 (Accepted) or 404 (Group not found) from DELETE /groups/:id
        """
        return api.generate_delete_request(host, token, "groups/{}".format(id))

    def remove_member(self, gid, uid, host, token):
        """
        Removes member from group

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#remove-a-member-from-a-group-or-project

            :param: id: (int) GitLab group ID
            :param: user_id: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 202 (accepted) or 404 (Member not found) from DELETE /groups/:id/members/:user_id
        """
        return api.generate_delete_request(host, token, "groups/%d/members/%d" % (gid, uid))

    def get_notification_level(self, host, token, id):
        """
        Get current group notification settings

        GitLab API Doc: hhttps://docs.gitlab.com/ee/api/notification_settings.html#group--project-level-notification-settings

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: id: (int) GitLab group ID
            :return: Response object containing the response to GET /groups/:id/notification_settings
        """
        return api.generate_get_request(host, token, "groups/%d/notification_settings" % id)

    def update_notification_level(self, host, token, id, level):
        """
        Update current group notification settings

        GitLab API Doc: https://docs.gitlab.com/ee/api/notification_settings.html#update-groupproject-level-notification-settings

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: id: (int) GitLab group ID
            :param: level: (str) Current group notification level
            :return: Response object containing the response to PUT /groups/:id/notification_settings
        """
        return api.generate_put_request(host, token, "groups/%d/notification_settings?level=%s" % (id, level), data=None)

    def export_group(self, host, token, source_id, data, headers):
        """
        Export a group using the groups api

            :param: host: (str) The source host
            :param: token: (str) A token that can access the source host with export permissions
            :param: source_id: (int) The group id on the source system
            :param: data: (str) Relevant data for the export
            :param: headers: (str) The headers for the API request
        """
        return api.generate_post_request(host, token, "groups/{}/export".format(source_id), data=data, headers=headers)

    def get_all_group_members_incl_inherited(self, id, host, token):
        """
        Gets a list of group or project members viewable by the authenticated user, including inherited members through ancestor groups

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project-including-inherited-members

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/members/all
        """
        return api.list_all(host, token, "groups/%d/members/all" % id)

    def get_all_group_issue_boards(self, id, host, token):
        """
        Lists Issue Boards in the given group

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_boards.html#list-all-group-issue-boards-in-a-group

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/boards
        """
        return api.list_all(host, token, "groups/%d/boards" % id)

    def get_group_issue_board(self, host, token, gid, bid):
        """
        Gets a single group issue board

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_boards.html#single-group-issue-board

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: gid: (int) GitLab group ID
            :param: bid: (str) Board ID
            :yield: Response object containing the response to GET /groups/:id/boards/:board_id
        """
        return api.generate_get_request(host, token, "groups/{0}/boards/{1}".format(gid, bid))

    def get_all_group_labels(self, id, host, token):
        """
        Get all labels for a given group

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_labels.html#group-labels-api

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/labels
        """
        return api.list_all(host, token, "groups/%d/labels" % id)

    def get_group_label(self, host, token, gid, lid):
        """
        Get a single label for a given group

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_labels.html#get-a-single-group-label

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: gid: (int) GitLab group ID
            :param: lid: (int) Label ID
            :yield: Response object containing the response to GET /groups/:id/labels/:label_id
        """
        return api.generate_get_request(host, token, "groups/{0}/labels/{1}".format(gid, lid))

    def get_all_group_milestones(self, id, host, token):
        """
        Returns a list of group milestones

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_milestones.html#list-group-milestones

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/milestones
        """
        return api.list_all(host, token, "groups/%d/milestones" % id)

    def get_group_milestone(self, host, token, gid, mid):
        """
        Gets a single group milestone

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_milestones.html#get-single-milestone

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: gid: (int) GitLab group ID
            :param: mid: (int) Milestone ID
            :yield: Response object containing the response to GET /groups/:id/milestones/:milestone_id
        """
        return api.generate_get_request(host, token, "groups/{0}/milestones/{1}".format(gid, mid))

    def get_all_group_hooks(self, id, host, token):
        """
        Get a list of group hooks

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-group-hooks

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/hooks
        """
        return api.list_all(host, token, "groups/%d/hooks" % id)

    def get_group_hook(self, host, token, gid, hid):
        """
        Get a specific hook for a group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#get-group-hook

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: gid: (int) GitLab group ID
            :param: hid: (int) Hook ID
            :yield: Response object containing the response to GET /groups/:id/hooks/:hook_id
        """
        return api.generate_get_request(host, token, "groups/{0}/hooks/{1}".format(gid, hid))

    def get_all_group_projects(self, id, host, token):
        """
        Get a list of projects in this group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-a-groups-projects

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/projects
        """
        return api.list_all(host, token, "groups/%d/projects" % id)

    def get_all_group_subgroups(self, id, host, token):
        """
        Get a list of visible direct subgroups in a group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-a-groups-subgroups

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/subgroups
        """
        return api.list_all(host, token, "groups/%d/subgroups" % id)

    def get_all_group_audit_events(self, id, host, token):
        """
        Get a list of audit events for this group

        GitLab API Doc: https://docs.gitlab.com/ee/api/audit_events.html#retrieve-all-group-audit-events

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/audit_events
        """
        return api.list_all(host, token, "groups/%d/audit_events" % id)

    def get_group_audit_event(self, host, token, gid, aid):
        """
        Gets a single group audit event

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_milestones.html#get-single-milestone

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: gid: (int) GitLab group ID
            :param: aid: (int) Audit Event ID
            :yield: Response object containing the response to GET /groups/:id/audit_events/:audit_event_id
        """
        return api.generate_get_request(host, token, "groups/{0}/audit_events/{1}".format(gid, aid))
