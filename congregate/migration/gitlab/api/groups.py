import json

from urllib.parse import quote_plus
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
from congregate.migration.gitlab.api.users import UsersApi


class GroupsApi(GitLabApiWrapper):
    def __init__(self):
        super().__init__()
        self.users = UsersApi()

    def get_group(self, gid, host, token):
        """
        Get all details of a group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#details-of-a-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /groups/:id
        """
        return self.api.generate_get_request(host, token, f"groups/{gid}")

    def get_group_by_full_path(self, full_path, host, token):
        """
        Get all details of a group matching the full path

            :param: full_path: (string) URL encoded full path to a group
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/<full_path>
        """
        return self.api.generate_get_request(host, token, f"groups/{quote_plus(full_path)}")

    def search_for_group(self, name, host, token):
        """
        Get all groups that match your string in their name or path

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#search-for-group

            :param: name: (string) Group name or path
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups?search=:name
        """
        return self.api.list_all(host, token, f"groups?search={name}")

    def create_group(self, host, token, data, message=None):
        """
        Creates a new project group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#new-group

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the various data required for creating a group. Refer to the link above for specific examples
            :return: Response object containing the response to POST /groups
        """
        if not message:
            message = f"Creating group with payload {str(data)}"
        return self.api.generate_post_request(host, token, "groups", json.dumps(data), description=message)

    def add_member_to_group(self, gid, host, token, member, message=None):
        """
        Adds a member to a group or project

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#add-a-member-to-a-group-or-project

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: member: (dict) Object containing the member data. Refer to the link above for specific examples
            :return: Response object containing the response to POST /groups/:id/members
        """
        if not message:
            message = f"Adding member to {gid} with payload {str(member)}"
        return self.api.generate_post_request(host, token, f"groups/{gid}/members", json.dumps(member), description=message)

    def get_all_groups(self, host, token):
        """
        Get a list of visible groups for the authenticated user

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-groups

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups
        """
        return self.api.list_all(host, token, "groups")

    def get_all_group_enterprise_users(self, gid, host, token):
        """
        Lists all enterprise users for a given top-level group.

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_enterprise_users.html#list-all-enterprise-users

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /groups/:gid/enterprise_users
        """
        yield from self.api.list_all(host, token, f"groups/{gid}/enterprise_users")

    def get_all_group_members(self, gid, host, token):
        """
        Gets a list of group or project members viewable by the authenticated user.
        Returns only direct members and not inherited members through ancestors groups.

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /groups/:id/members
        """
        for member in self.api.list_all(host, token, f"groups/{gid}/members"):
            member["email"] = self.users.get_user_email(
                member["id"], host, token)
            yield member

    def get_all_group_members_incl_inherited(self, gid, host, token):
        """
        Gets a list of group members viewable by the authenticated user, including inherited members through ancestor groups

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project-including-inherited-and-invited-members

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/members/all
        """
        for member in self.api.list_all(host, token, f"groups/{gid}/members/all"):
            yield self.users.get_user(member["id"], host, token).json()

    def get_all_group_billable_members(self, gid, host, token):
        """
        Gets a list of group members that count as billable. The list includes members in subgroups and projects.

        This API endpoint works on top-level groups only. It does not work on subgroups.

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#list-all-billable-members-of-a-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/billable_members
        """
        for member in self.api.list_all(host, token, f"groups/{gid}/billable_members"):
            yield self.users.get_user(member["id"], host, token).json()

    def update_member_access_level(self, host, token, gid, mid, level, message=None):
        """
        Updates the access_level of a group member.

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#edit-a-member-of-a-group-or-project

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: gid: (int) GitLab group ID
            :param: mid: (int) GitLab group member ID
            :param: level: (int) GitLab group member access level
            :yield: Response object containing the response to PUT /groups/:gid/members/:mid
        """
        return self.api.generate_put_request(host, token, f"groups/{gid}/members/{mid}?access_level={level}", data=None, description=message)

    def get_all_subgroups(self, gid, host, token):
        """
        Get a list of visible direct subgroups in this group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-a-groups-subgroups

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /groups/:id/subgroups

        """
        return self.api.list_all(host, token, f"groups/{gid}/subgroups")

    def delete_group(self, gid, host, token, full_path=None, permanent=False):
        """
        Removes group with all projects inside

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#remove-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 202 (Accepted) or 404 (Group not found) from DELETE /groups/:id
        """
        message = f"Deleting destination group {gid}"
        if permanent and full_path:
            message += f" '{full_path}' permanently"
            return self.api.generate_delete_request(host, token, f"groups/{gid}?&full_path={quote_plus(full_path)}&permanently_remove=true", description=message)
        return self.api.generate_delete_request(host, token, f"groups/{gid}", description=message)

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
        return self.api.generate_delete_request(host, token, f"groups/{gid}/members/{uid}")

    def get_notification_level(self, host, token, gid):
        """
        Get current group notification settings

        GitLab API Doc: hhttps://docs.gitlab.com/ee/api/notification_settings.html#group--project-level-notification-settings

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: gid: (int) GitLab group ID
            :return: Response object containing the response to GET /groups/:id/notification_settings
        """
        return self.api.generate_get_request(host, token, f"groups/{gid}/notification_settings")

    def export_group(self, host, token, gid, data=None, headers=None, message=None):
        """
        Export a group using the groups api

            :param: host: (str) The source host
            :param: token: (str) A token that can access the source host with export permissions
            :param: gid: (int) The group id on the source system
            :param: data: (str) Relevant data for the export
            :param: headers: (str) The headers for the API request
        """
        return self.api.generate_post_request(host, token, f"groups/{gid}/export", data=data, headers=headers, description=message)

    def get_group_download_status(self, host, token, gid):
        """
        Download the finished export

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_import_export.html#export-download

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: gid: (int) GitLab group ID
            :return: The exported archive
        """
        return self.api.generate_get_request(host, token, f"groups/{gid}/export/download")

    def import_group(self, host, token, data=None, files=None, headers=None, message=None):
        """
        Import a group using the groups api

            :param: host: (str) The destination host
            :param: token: (str) A token that can access the destination host with import permissions
            :param: files: (str) The group filename as it was exported
            :param: data: (str) Relevant data for the export
            :param: headers: (str) The headers for the API request
        """
        if not message:
            message = f"Importing group with payload {str(data)}"
        return self.api.generate_post_request(host, token, "groups/import", data=data, files=files, headers=headers, description=message)

    def bulk_group_import(self, host, token, data=None, message=None):
        """
        Start a new GitLab migration

        GitLab API Doc: https://docs.gitlab.com/ee/api/bulk_imports.html#start-a-new-gitlab-migration

            :param: host: (str) The destination host
            :param: token: (str) A token that can access the destination host with import permissions
            :param: data: (str) Relevant data for the import
        """
        if not message:
            clean_data = data.copy()
            clean_data.pop("configuration")
            message = f"Importing groups in bulk with payload {str(clean_data)}"
        return self.api.generate_post_request(host, token, "bulk_imports", data=json.dumps(data), description=message)

    def get_bulk_group_import_status(self, host, token, bid):
        """
        Get GitLab migration details

        GitLab API Doc: https://docs.gitlab.com/ee/api/bulk_imports.html#get-gitlab-migration-details

            :param: bid: (int) GitLab bulk import ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /bulk_imports/:id
        """
        return self.api.generate_get_request(host, token, f"bulk_imports/{bid}")

    def get_all_bulk_group_import_entities(self, host, token, bid):
        """
        List GitLab migration entities

        GitLab API Doc: https://docs.gitlab.com/ee/api/bulk_imports.html#list-gitlab-migration-entities

            :param: bid: (int) GitLab bulk import ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /bulk_imports/:bid/entities
        """
        return self.api.list_all(host, token, f"bulk_imports/{bid}/entities")

    def get_all_group_issue_boards(self, gid, host, token):
        """
        Lists Issue Boards in the given group

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_boards.html#list-all-group-issue-boards-in-a-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/boards
        """
        return self.api.list_all(host, token, f"groups/{gid}/boards")

    def get_all_group_labels(self, gid, host, token):
        """
        Get all labels for a given group

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_labels.html#group-labels-api

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/labels
        """
        return self.api.list_all(host, token, f"groups/{gid}/labels?include_ancestor_groups=false")

    def get_all_group_milestones(self, gid, host, token):
        """
        Returns a list of group milestones

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_milestones.html#list-group-milestones

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/milestones
        """
        return self.api.list_all(host, token, f"groups/{gid}/milestones")

    def get_all_group_hooks(self, gid, host, token):
        """
        Get a list of group hooks

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-group-hooks

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/hooks
        """
        return self.api.list_all(host, token, f"groups/{gid}/hooks")

    def add_group_hook(self, host, token, gid, data, message=None):
        """
        Add a hook to a specified group

        GitLab API doc: https://docs.gitlab.com/ee/api/groups.html#add-group-hook

            :param: gid: (int) GitLab group ID
            :param: data: (dict) Object containing the various data required for creating a hook. Refer to the link above for specific examples
            :return: Response object containing the response to POST /groups/:id/hooks
        """
        if not message:
            message = "Adding group hook"
        return self.api.generate_post_request(host, token, f"groups/{gid}/hooks", json.dumps(data), description=message)

    def share_group(self, host, token, gid, data, message=None):
        """
        Share groups with groups

        GitLab API doc: https://docs.gitlab.com/ee/api/groups.html#share-groups-with-groups

            :param: id: (int/string) The ID or URL-encoded path of the group
            :param: gid: (int) The ID of the group to share with
            :param: data: (dict) Object containing the various data required for sharing a group. Refer to the link above for specific examples
            :return: Response object containing the response to POST /groups/:id/share
        """
        if not message:
            message = f"Sharing source group '{data}' with destination group id '{gid}' "
        return self.api.generate_post_request(host, token, f"groups/{gid}/share", json.dumps(data), description=message)

    def get_all_group_projects(self, gid, host, token, include_subgroups=False, with_shared=False):
        """
        Get a list of projects in this group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-a-groups-projects

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: include_subgroups: (bool) Include projects in subgroups of this group. Default is false
            :param: with_shared: (bool) Include projects shared to this group. Default is true
            :yield: Generator returning JSON of each result from GET /groups/:id/projects
        """
        return self.api.list_all(host, token, f"groups/{gid}/projects?include_subgroups={include_subgroups}&with_shared={with_shared}")

    def get_all_group_projects_count(self, gid, host, token, include_subgroups=False, with_shared=False):
        """
        Get a total count of projects in this group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-a-groups-projects

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: include_subgroups: (bool) Include projects in subgroups of this group. Default is false
            :param: with_shared: (bool) Include projects shared to this group. Default is true
            :yield: Generator returning JSON of each result from GET /groups/:id/projects
        """
        return self.api.get_count(host, token, f"groups/{gid}/projects?include_subgroups={include_subgroups}&with_shared={with_shared}")

    def get_all_group_subgroups(self, gid, host, token):
        """
        Get a list of visible direct subgroups in a group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-a-groups-subgroups

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/subgroups
        """
        return self.api.list_all(host, token, f"groups/{gid}/subgroups")

    def get_all_group_subgroups_count(self, gid, host, token):
        """
        Get a list of visible direct subgroups in a group

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-a-groups-subgroups

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/subgroups
        """
        return self.api.get_count(host, token, f"groups/{gid}/subgroups")

    def get_all_descendant_groups(self, gid, host, token):
        """
        Get a list of visible descendant groups of this group.

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#list-descendant-groups

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/descendant_groups
        """
        return self.api.list_all(host, token, f"groups/{gid}/descendant_groups")

    def get_all_group_audit_events(self, gid, host, token):
        """
        Get a list of audit events for this group

        GitLab API Doc: https://docs.gitlab.com/ee/api/audit_events.html#retrieve-all-group-audit-events

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/audit_events
        """
        return self.api.list_all(host, token, f"groups/{gid}/audit_events")

    def get_all_group_registry_repositories(self, gid, host, token):
        """
        Get a list of registry repositories in a group

        GitLab API Doc: https://docs.gitlab.com/ee/api/container_registry.html#within-a-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/registry/repositories
        """
        return self.api.list_all(host, token, f"groups/{gid}/registry/repositories")

    def get_all_group_epics(self, gid, host, token):
        """
        Gets all epics of the requested group and its subgroups

        GitLab API Doc: https://docs.gitlab.com/ee/api/epics.html#list-epics-for-a-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/epics
        """
        return self.api.list_all(host, token, f"groups/{gid}/epics")

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
        return self.api.list_all(host, token, f"groups/{gid}/epics/{eid}/notes")

    def get_all_group_custom_attributes(self, gid, host, token):
        """
        Get all custom attributes on a group

        GitLab API Doc: https://docs.gitlab.com/ee/api/custom_attributes.html#list-custom-attributes

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/custom_attributes
        """
        return self.api.list_all(host, token, f"groups/{gid}/custom_attributes")

    def get_all_group_variables(self, gid, host, token):
        """
        Get list of a variables for the given group

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_level_variables.html

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/variables
        """
        return self.api.list_all(host, token, f"groups/{gid}/variables")

    def create_group_variable(self, gid, host, token, data, message=None):
        """
        Creates a new group variable

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_level_variables.html#create-variable

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the various data required for creating a group variable. Refer to the link above for specific examples
            :return: Response object containing the response to POST /groups/:id/variables
        """
        if not message:
            message = f"Creating new variable for group {gid}"
        return self.api.generate_post_request(host, token, f"groups/{gid}/variables", json.dumps(data), description=message)

    def get_all_group_badges(self, gid, host, token):
        """
        Gets a list of all badges for a given group

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_badges.html#list-all-badges-of-a-group

            :param: gid: (int) GitLab group ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /groups/:id/badges
        """
        return self.api.list_all(host, token, f"groups/{gid}/badges")

    def create_group_access_token(self, gid, host, token, data, message=None):
        """
        Create a group access token. You must have the Owner role for the group to create group access tokens.

        GitLab API Doc: https://docs.gitlab.com/ee/api/group_access_tokens.html#create-a-group-access-token

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the various data required for creating a group access token.
                Refer to the link above for specific examples.
            :return: Response object containing the response to POST groups/:id/access_tokens
        """
        if not message:
            message = f"Creating group access token with payload {str(data)}"
        return self.api.generate_post_request(host, token, f"groups/{gid}/access_tokens", json.dumps(data), description=message)

    def update_group(self, gid, host, token, data=None, message=None):
        """
        Updates the project group. Only available to group owners and administrators.

        GitLab API Doc: https://docs.gitlab.com/ee/api/groups.html#update-group

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: gid: (int) GitLab group ID
            :yield: Response object containing the response to PUT /groups/:gid
        """
        if not message:
            message = f"Editing group {gid} with payload {str(data)}"
        return self.api.generate_put_request(host, token, f"groups/{gid}", json.dumps(data), description=message)
