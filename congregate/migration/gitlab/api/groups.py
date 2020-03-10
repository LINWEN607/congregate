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

    def add_member_to_group(self, gid, host, token, member):
        """
        Adds a member to a group or project

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#add-a-member-to-a-group-or-project

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: member: (dict) Object containing the member data. Refer to the link above for specific examples
            :return: Response object containing the response to POST /groups/:id/members
        """
        return api.generate_post_request(host, token, "groups/%d/members" % gid, json.dumps(member))

    def get_all_groups(self, host, token):
        """
        Get a list of visible groups for the authenticated user

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-groups

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups
        """
        return api.list_all(host, token, "groups")

    def get_all_group_members(self, gid, host, token):
        """
        https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /groups/:id/members
        """
        return api.list_all(host, token, "groups/%d/members" % gid)

    def update_member_access_level(self, host, token, gid, uid, level):
        return api.generate_put_request(host, token, "groups/{0}/members/{1}?access_level={2}".format(gid, uid, level), data=None)

    def get_all_subgroups(self, gid, host, token):
        """
        Get a list of visible direct subgroups in this group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-a-groups-subgroups

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /groups/:id/subgroups

        """
        return api.list_all(host, token, "groups/%d/subgroups" % gid)

    def delete_group(self, gid, host, token):
        """
        Removes group with all projects inside

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#remove-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 202 (Accepted) or 404 (Group not found) from DELETE /groups/:id
        """
        return api.generate_delete_request(host, token, "groups/{}".format(gid))

    def remove_member(self, gid, uid, host, token):
        """
        Removes member from group

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#remove-a-member-from-a-group-or-project

            :param: gid: (int) GitLab group ID
            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 202 (accepted) or 404 (Member not found) from DELETE /groups/:id/members/:user_id
        """
        return api.generate_delete_request(host, token, "groups/%d/members/%d" % (gid, uid))

    def get_notification_level(self, host, token, gid):
        """
        Get current group notification settings

        GitLab API Doc: hhttps://docs.gitlab.com/ee/api/notification_settings.html#group--project-level-notification-settings

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: gid: (int) GitLab group ID
            :return: Response object containing the response to GET /groups/:id/notification_settings
        """
        return api.generate_get_request(host, token, "groups/%d/notification_settings" % gid)

    def export_group(self, host, token, gid, data=None, headers=None):
        """
        Export a group using the groups api

            :param: host: (str) The source host
            :param: token: (str) A token that can access the source host with export permissions
            :param: gid: (int) The group id on the source system
            :param: data: (str) Relevant data for the export
            :param: headers: (str) The headers for the API request
        """
        return api.generate_post_request(host, token, "groups/{}/export".format(gid), data=data, headers=headers)

    def get_group_download_status(self, host, token, gid):
        """
        Download the finished export

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_import_export.html#export-download

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: gid: (int) GitLab group ID
            :return: The exported archive
        """
        return api.generate_get_request(host, token, "groups/%d/export/download" % gid)

    def import_group(self, host, token, data=None, files=None, headers=None):
        """
        Import a group using the groups api

            :param: host: (str) The destination host
            :param: token: (str) A token that can access the destination host with import permissions
            :param: files: (str) The group filename as it was exported
            :param: data: (str) Relevant data for the export
            :param: headers: (str) The headers for the API request
        """
        return api.generate_post_request(host, token, "groups/import", data=data, files=files, headers=headers)

    def get_all_group_members_incl_inherited(self, gid, host, token):
        """
        Gets a list of group members viewable by the authenticated user, including inherited members through ancestor groups

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project-including-inherited-members

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/members/all
        """
        return api.list_all(host, token, "groups/%d/members/all" % gid)

    def get_all_group_issue_boards(self, gid, host, token):
        """
        Lists Issue Boards in the given group

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_boards.html#list-all-group-issue-boards-in-a-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/boards
        """
        return api.list_all(host, token, "groups/%d/boards" % gid)

    def get_all_group_labels(self, gid, host, token):
        """
        Get all labels for a given group

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_labels.html#group-labels-api

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/labels
        """
        return api.list_all(host, token, "groups/%d/labels" % gid)

    def get_all_group_milestones(self, gid, host, token):
        """
        Returns a list of group milestones

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_milestones.html#list-group-milestones

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/milestones
        """
        return api.list_all(host, token, "groups/%d/milestones" % gid)

    def get_all_group_hooks(self, gid, host, token):
        """
        Get a list of group hooks

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-group-hooks

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/hooks
        """
        return api.list_all(host, token, "groups/%d/hooks" % gid)

    def get_all_group_projects(self, gid, host, token):
        """
        Get a list of projects in this group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-a-groups-projects

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/projects
        """
        return api.list_all(host, token, "groups/%d/projects" % gid)

    def get_all_group_subgroups(self, gid, host, token):
        """
        Get a list of visible direct subgroups in a group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-a-groups-subgroups

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/subgroups
        """
        return api.list_all(host, token, "groups/%d/subgroups" % gid)

    def get_all_group_audit_events(self, gid, host, token):
        """
        Get a list of audit events for this group

        GitLab API Doc: https://docs.gitlab.com/ee/api/audit_events.html#retrieve-all-group-audit-events

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/audit_events
        """
        return api.list_all(host, token, "groups/%d/audit_events" % gid)

    def get_all_group_registry_repositories(self, id, host, token):
        """
        Get a list of registry repositories in a group

        GitLab API Doc: https://docs.gitlab.com/ee/api/container_registry.html#within-a-group

            :param: id: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/registry/repositories
        """
        return api.list_all(host, token, "groups/%d/registry/repositories" % id)

    def get_all_group_epics(self, gid, host, token):
        """
        Gets all epics of the requested group and its subgroups

        GitLab API Doc: https://docs.gitlab.com/ee/api/epics.html#list-epics-for-a-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/epics
        """
        return api.list_all(host, token, "groups/%d/epics" % gid)

    def get_group_epic_notes(self, gid, eid, host, token):
        """
        Gets a list of all notes for a single epic

        GitLab API Doc: https://docs.gitlab.com/ee/api/notes.html#list-all-epic-notes

            :param: gid: (int) GitLab group ID
            :param: eid: (int) Epic ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/epics/:epic_id/notes
        """
        return api.list_all(host, token, "groups/%d/epics/%d/notes" % (gid, eid))

    def get_all_group_custom_attributes(self, gid, host, token):
        """
        Get all custom attributes on a group

        https://docs.gitlab.com/ee/api/custom_attributes.html#list-custom-attributes

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/custom_attributes
        """
        return api.list_all(host, token, "groups/%d/custom_attributes" % gid)

    def get_all_group_variables(self, gid, host, token):
        """
        Get list of a variables for the given group

        https://docs.gitlab.com/ee/api/group_level_variables.html

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/variables
        """
        return api.generate_get_request(host, token, "groups/%d/variables" % gid)

    def create_group_variable(self, gid, host, token, data):
        """
        Creates a new group variable

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_level_variables.html#create-variable

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the various data required for creating a group variable. Refer to the link above for specific examples
            :return: Response object containing the response to POST /groups/:id/variables
        """
        return api.generate_post_request(host, token, "groups/%d/variables" % gid, json.dumps(data))

    def get_all_group_badges(self, gid, host, token):
        """
        Gets a list of all badges for a given group

        https://docs.gitlab.com/ee/api/group_badges.html#list-all-badges-of-a-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/badges
        """
        return api.list_all(host, token, "groups/%d/badges" % gid)
