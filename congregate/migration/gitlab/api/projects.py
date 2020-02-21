import json
from urllib import quote_plus
from congregate.helpers import api


class ProjectsApi():

    def search_for_project(self, host, token, name):
        """
        Search for projects by name which are accessible to the authenticated user

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#search-for-projects-by-name

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: name: (str) GitLab project name
            :yield: Generator containing JSON results from GET /projects?search=:name

        """
        return api.list_all(host, token, "projects?search=%s" % quote_plus(name))

    def get_project(self, id, host, token):
        """
        Get a specific project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#get-single-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/:id

        """
        return api.generate_get_request(host, token, "projects/%d" % id)

    def get_project_by_path_with_namespace(self, path, host, token):
        """
        Get all details of a project matching the path_with_namespace

            :param: path: (string) URL encoded path to a project
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/<path>
        """
        return api.generate_get_request(host, token, "projects/{}".format(quote_plus(path)))

    def get_all_projects(self, host, token, statistics=False):
        """
        Get a list of all visible projects across GitLab for the authenticated user

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-all-projects

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator containing JSON results from GET /projects

        """
        return api.list_all(host, token, "projects{}".format("?statistics=true" if statistics else ""))

    def get_members(self, id, host, token):
        """
        Gets a list of group or project members viewable by the authenticated user

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator containing JSON results from GET /projects

        """
        return api.list_all(host, token, "projects/%d/members" % id)

    def add_member(self, id, host, token, member):
        """
        Adds a member to a group or project

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#add-a-member-to-a-group-or-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: member: (dict) Object containing the member data. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:id/members

        """
        return api.generate_post_request(host, token, "projects/%d/members" % id, json.dumps(member))

    def remove_member(self, id, user_id, host, token):
        """
        Removes member from project

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#remove-a-member-from-a-group-or-project

            :param: id: (int) GitLab project ID
            :param: user_id: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 202 (accepted) or 404 (Member not found) from DELETE /projects/:id/members/:user_id
        """
        return api.generate_delete_request(host, token, "projects/%d/members/%d" % (id, user_id))

    def archive_project(self, host, token, id):
        """
        Archives the project if the user is either admin or the project owner of this project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#archive-a-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/archive

        """
        return api.generate_post_request(host, token, "projects/%d/archive" % id, {}).json()

    def unarchive_project(self, host, token, id):
        """
        Unarchives the project if the user is either admin or the project owner of this project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#unarchive-a-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/unarchive

        """
        return api.generate_post_request(host, token, "projects/%d/unarchive" % id, {}).json()

    def delete_project(self, host, token, id):
        """
        Removes a project including all associated resources

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#remove-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 202 (Accepted) or 404 (Project not found) from DELETE /projects/:id
        """
        return api.generate_delete_request(host, token, "projects/{}".format(id))

    def add_shared_group(self, host, token, pid, group):
        """
        Allow to share project with group

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#share-project-with-group

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: group: (dict) Object containing the necessary data for the shared group
            :return: Response object containing the response to POST /projects/:id/share

        """
        return api.generate_post_request(host, token, "projects/%d/share" % pid, json.dumps(group))

    def edit_project(self, host, token, pid, data=None):
        """
        Edit a project

        GitLab API doc: https://docs.gitlab.com/ee/api/projects.html#edit-project

            :param: id: (int) GitLab project ID
            :return: Response object containing the response to PUT /projects/:id
        """
        return api.generate_put_request(host, token, "projects/{}".format(pid), data=data)

    def start_pull_mirror(self, host, token, pid, data=None):
        """
        Start the pull mirroring process for a Project
        GitLab API doc: https://docs.gitlab.com/ee/api/projects.html#start-the-pull-mirroring-process-for-a-project-starter

            :param: id: (int) GitLab project ID
            :return: Response object containing the response to PUT /projects/:id/mirror/pull
        """
        return api.generate_post_request(host, token, "projects/{}/mirror/pull".format(pid), json.dumps(data))

    def create_project(self, host, token, name, data=None, headers=None):
        if data is not None:
            data["name"] = name
        else:
            data = {"name": name}
        return api.generate_post_request(host, token, "projects", json.dumps(data), headers=headers)

    def export_project(self, host, token, pid, data=None, headers=None):
        """
        Schedule an export
        GitLab API doc: https://docs.gitlab.com/ee/api/project_import_export.html#schedule-an-export

            :param: pid: (int) GitLab project ID
            :return: Response object containing the response to POST /projects/:id/export
        """
        return api.generate_post_request(host, token, "projects/{}/export".format(pid), data=data, headers=headers)

    def import_project(self, host, token, data=None, files=None, headers=None):
        """
        Import a project using the Projects export/import API

            :param: host: (str) The destination host
            :param: token: (str) A token that can access the destination host with import permissions
            :param: files: (str) The project filename as it was exported
            :param: data: (str) Relevant data for the export
            :param: headers: (str) The headers for the API request
        """
        return api.generate_post_request(host, token, "projects/import", data=data, files=files, headers=headers)

    def get_all_project_users(self, id, host, token):
        """
        Get the users list of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#get-project-users

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/users
        """
        return api.list_all(host, token, "projects/%d/users" % id)

    def get_all_project_forks(self, id, host, token):
        """
        List the projects accessible to the calling user that have an established, forked relationship with the specified project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-forks-of-a-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/forks
        """
        return api.list_all(host, token, "projects/%d/forks" % id)

    def get_all_project_members_incl_inherited(self, id, host, token):
        """
        Gets a list of project members viewable by the authenticated user, including inherited members through ancestor groups

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project-including-inherited-members

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/members/all
        """
        return api.list_all(host, token, "projects/%d/members/all" % id)

    def get_all_project_starrers(self, id, host, token):
        """
        List the users who starred the specified project

        https://docs.gitlab.com/ee/api/projects.html#list-starrers-of-a-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/starrers
        """
        return api.list_all(host, token, "projects/%d/starrers" % id)

    def get_all_project_starrers(self, id, host, token):
        """
        Gets a list of a project’s badges and its group badges

        https://docs.gitlab.com/ee/api/project_badges.html#project-badges-api

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/badges
        """
        return api.list_all(host, token, "projects/%d/badges" % id)

    def get_all_project_issues(self, id, host, token):
        """
        Get a list of a project’s issues

        https://docs.gitlab.com/ee/api/issues.html#list-project-issues

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues
        """
        return api.list_all(host, token, "projects/%d/issues" % id)

    def get_all_project_issue_notes(self, pid, iid, host, token):
        """
        Gets a list of all notes for a given issue

        https://docs.gitlab.com/ee/api/notes.html#list-project-issue-notes

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues/:issue_iid/notes
        """
        return api.list_all(host, token, "projects/{0}/issues/{1}/notes".format(pid, iid))

    def get_all_project_boards(self, id, host, token):
        """
        Lists Issue Boards in the given project

        https://docs.gitlab.com/ee/api/boards.html#project-board

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/boards
        """
        return api.list_all(host, token, "projects/%d/boards" % id)

    def get_all_project_labels(self, id, host, token):
        """
        Get all labels for a given project

        https://docs.gitlab.com/ee/api/labels.html#list-labels

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/labels
        """
        return api.list_all(host, token, "projects/%d/labels" % id)

    def get_all_project_milestones(self, id, host, token):
        """
        Returns a list of project milestones

        https://docs.gitlab.com/ee/api/milestones.html#list-project-milestones

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/milestones
        """
        return api.list_all(host, token, "projects/%d/milestones" % id)

    def get_all_project_releases(self, id, host, token):
        """
        Returns a paginated list of given project's releases

        https://docs.gitlab.com/ee/api/releases/#list-releases

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/releases
        """
        return api.list_all(host, token, "projects/%d/releases" % id)

    def get_all_project_events(self, id, host, token):
        """
        Get a list of visible events for a particular project

        https://docs.gitlab.com/ee/api/events.html#list-a-projects-visible-events

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:project_id/events
        """
        return api.list_all(host, token, "projects/%d/events" % id)

    def get_all_project_variables(self, id, host, token):
        """
        Get list of a project’s variables

        https://docs.gitlab.com/ee/api/project_level_variables.html#list-project-variables

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/variables
        """
        return api.list_all(host, token, "projects/%d/variables" % id)

    def get_all_project_protected_branches(self, id, host, token):
        """
        Gets a list of protected branches from a project

        https://docs.gitlab.com/ee/api/protected_branches.html#list-protected-branches

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/protected_branches
        """
        return api.list_all(host, token, "projects/%d/protected_branches" % id)

    def get_all_project_protected_environments(self, id, host, token):
        """
        Gets a list of protected environments from a project

        https://docs.gitlab.com/ee/api/protected_environments.html#list-protected-environments

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/protected_environments
        """
        return api.list_all(host, token, "projects/%d/protected_environments" % id)

    def get_all_project_protected_tags(self, id, host, token):
        """
        Gets a list of protected tags from a project

        https://docs.gitlab.com/ee/api/protected_tags.html#list-protected-tags

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/protected_tags
        """
        return api.list_all(host, token, "projects/%d/protected_tags" % id)

    def get_all_project_deploy_keys(self, id, host, token):
        """
        Get a list of a project’s deploy keys

        https://docs.gitlab.com/ee/api/deploy_keys.html#list-project-deploy-keys

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/deploy_keys
        """
        return api.list_all(host, token, "projects/%d/deploy_keys" % id)
