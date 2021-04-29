import json
from urllib.parse import quote_plus
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper
from congregate.migration.gitlab.api.users import UsersApi


class ProjectsApi(GitLabApiWrapper):
    def __init__(self):
        super().__init__()
        self.users = UsersApi()

    def search_for_project(self, host, token, name):
        """
        Search for projects by name which are accessible to the authenticated user

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: name: (str) GitLab project name
            :yield: Generator containing JSON results from GET /projects?search=:name

        """
        return self.api.list_all(host, token, f"projects?search={quote_plus(name)}")

    def get_project(self, pid, host, token):
        """
        Get a specific project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#get-single-project

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/:id

        """
        return self.api.generate_get_request(host, token, f"projects/{pid}")

    def get_project_by_path_with_namespace(self, path, host, token):
        """
        Get all details of a project matching the path_with_namespace

            :param: path: (string) URL encoded path to a project
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/<path>
        """
        return self.api.generate_get_request(host, token, f"projects/{quote_plus(path)}")

    def get_all_projects(self, host, token, statistics=False):
        """
        Get a list of all visible projects across GitLab for the authenticated user

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-all-projects

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator containing JSON results from GET /projects

        """
        return self.api.list_all(host, token, "projects{}".format("?statistics=true" if statistics else ""), keyset=False)

    def get_members(self, id, host, token):
        """
        Gets a list of group or project members viewable by the authenticated user

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator containing JSON results from GET /projects

        """
        for member in self.api.list_all(host, token, f"projects/{id}/members"):
            member["email"] = self.users.get_user_email(
                member["id"], host, token)
            yield member

    def add_member(self, id, host, token, member, message=None):
        """
        Adds a member to a group or project

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: member: (dict) Object containing the member data. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:id/members

        """
        if not message:
            message = ("Adding user {0} to project {1}").format(
                member["user_id"], id)
        return self.api.generate_post_request(host, token, f"projects/{id}/members", json.dumps(member), description=message)

    def create_new_project_deploy_key(self, pid, host, token, key, message=None):
        """
        Creates a new deploy key for a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/deploy_keys.html#add-deploy-key

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: key: (dict) Object containing the key data. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:id/deploy_keys

        """
        if not message:
            message = "Creating new deploy key"
        return self.api.generate_post_request(host, token, f"projects/{pid}/deploy_keys", json.dumps(key), description=message)

    def remove_member(self, pid, uid, host, token, message=None):
        """
        Removes member from project

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html

            :param: pid: (int) GitLab project ID
            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 202 (accepted) or 404 (Member not found) from DELETE /projects/:id/members/:user_id
        """
        if not message:
            message = "Deleting member from project"
        return self.api.generate_delete_request(host, token, f"projects/{pid}/members/{uid}", description=message)

    def archive_project(self, host, token, pid, message=None):
        """
        Archives the project if the user is either admin or the project owner of this project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#archive-a-project

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/archive

        """
        if not message:
            message = "Archiving project"
        return self.api.generate_post_request(host, token, f"projects/{pid}/archive", {}, description=message)

    def unarchive_project(self, host, token, id, message=None):
        """
        Unarchives the project if the user is either admin or the project owner of this project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#unarchive-a-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/unarchive

        """
        if not message:
            message = "Unarchiving project"
        return self.api.generate_post_request(host, token, f"projects/{id}/unarchive", {}, description=message)

    def delete_project(self, host, token, id):
        """
        Removes a project including all associated resources

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#remove-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 202 (Accepted) or 404 (Project not found) from DELETE /projects/:id
        """
        message = "Deleting project"
        return self.api.generate_delete_request(host, token, f"projects/{id}", description=message)

    def add_shared_group(self, host, token, pid, data=None, message=None):
        """
        Allow to share project with group

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#share-project-with-group

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: group: (dict) Object containing the necessary data for the shared group
            :return: Response object containing the response to POST /projects/:id/share

        """
        if not message:
            message = "Sharing project %d with group %d" % (
                pid, data["group_id"])
        return self.api.generate_post_request(host, token, f"projects/{pid}/share", json.dumps(data), description=message)

    def edit_project(self, host, token, pid, data=None):
        """
        Edit a project

        GitLab API doc: https://docs.gitlab.com/ee/api/projects.html#edit-project

            :param: id: (int) GitLab project ID
            :return: Response object containing the response to PUT /projects/:id
        """
        return self.api.generate_put_request(host, token, f"projects/{pid}", data=json.dumps(data))

    def start_pull_mirror(self, host, token, pid, data=None):
        """
        Start the pull mirroring process for a Project

        GitLab API doc: https://docs.gitlab.com/ee/api/projects.html

            :param: id: (int) GitLab project ID
            :return: Response object containing the response to PUT /projects/:id/mirror/pull
        """
        return self.api.generate_post_request(host, token, f"projects/{pid}/mirror/pull", json.dumps(data))

    def create_project(self, host, token, name, data=None, headers=None, message=None):
        if data is not None:
            data["name"] = name
        else:
            data = {"name": name}
        if not message:
            message = "Creating project %s with payload %s" % (name, str(data))
        return self.api.generate_post_request(host, token, "projects", json.dumps(data), headers=headers, description=message)

    def export_project(self, host, token, pid, data=None, headers=None, message=None):
        """
        Schedule an export

        GitLab API doc: https://docs.gitlab.com/ee/api/project_import_export.html#schedule-an-export

            :param: pid: (int) GitLab project ID
            :return: Response object containing the response to POST /projects/:id/export
        """
        if not message:
            message = "Exporting project"
        return self.api.generate_post_request(host, token, f"projects/{pid}/export", data=data, headers=headers, description=message)

    def get_project_export_status(self, id, host, token):
        """
        Get the status of export

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_import_export.html#export-status

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:id/export
        """
        return self.api.generate_get_request(host, token, f"projects/{id}/export")

    def import_project(self, host, token, data=None, files=None, headers=None, message=None):
        """
        Import a project using the Projects export/import API

            :param: host: (str) The destination host
            :param: token: (str) A token that can access the destination host with import permissions
            :param: files: (str) The project filename as it was exported
            :param: data: (str) Relevant data for the export
            :param: headers: (str) The headers for the API request
        """
        if not message:
            message = "Importing project with payload %s" % str(data)
        return self.api.generate_post_request(host, token, "projects/import", data=data, files=files, headers=headers, description=message)

    def get_project_import_status(self, host, token, pid):
        """
        Get the status of an import

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_import_export.html#import-status

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:id/import
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/import")

    def get_all_project_users(self, id, host, token):
        """
        Get the users list of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#get-project-users

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/users
        """
        return self.api.list_all(host, token, f"projects/{id}/users")

    def get_all_project_forks(self, id, host, token):
        """
        List the projects accessible to the calling user that have an established, forked relationship with the specified project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-forks-of-a-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/forks
        """
        return self.api.list_all(host, token, f"projects/{id}/forks")

    def get_all_project_members_incl_inherited(self, id, host, token):
        """
        Gets a list of project members viewable by the authenticated user, including inherited members through ancestor groups

        GitLab API Doc: GitLab API Doc: https://docs.gitlab.com/ee/api/members.html

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/members/all
        """
        for member in self.api.list_all(host, token, f"projects/{id}/members/all"):
            member["email"] = self.users.get_user_email(
                member["id"], host, token)
            yield member

    def get_all_project_starrers(self, id, host, token):
        """
        List the users who starred the specified project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-starrers-of-a-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/starrers
        """
        return self.api.list_all(host, token, f"projects/{id}/starrers")

    def get_all_project_badges(self, pid, host, token):
        """
        Gets a list of a project badges and its group badges

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_badges.html#project-badges-api

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/badges
        """
        return self.api.list_all(host, token, f"projects/{pid}/badges")

    def get_all_project_boards(self, pid, host, token):
        """
        Lists Issue Boards in the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/boards.html#project-board

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/boards
        """
        return self.api.list_all(host, token, f"projects/{pid}/boards")

    def get_all_project_labels(self, id, host, token):
        """
        Get all labels for a given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/labels.html#list-labels

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/labels
        """
        return self.api.list_all(host, token, f"projects/{id}/labels")

    def get_all_project_milestones(self, id, host, token):
        """
        Returns a list of project milestones

        GitLab API Doc: https://docs.gitlab.com/ee/api/milestones.html#list-project-milestones

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/milestones
        """
        return self.api.list_all(host, token, f"projects/{id}/milestones")

    def get_all_project_issues(self, id, host, token):
        """
        Returns a list of project issues

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-project-issues

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues
        """
        return self.api.list_all(host, token, f"projects/{id}/issues")

    def get_all_project_releases(self, id, host, token):
        """
        Returns a paginated list releases for a given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/releases/#list-releases

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/releases
        """
        return self.api.list_all(host, token, f"projects/{id}/releases")

    def get_all_project_events(self, pid, host, token):
        """
        Get a list of visible events for a particular project

        GitLab API Doc: https://docs.gitlab.com/ee/api/events.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:project_id/events
        """
        return self.api.list_all(host, token, f"projects/{pid}/events")

    def get_all_project_variables(self, pid, host, token):
        """
        Get list of variables for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_level_variables.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:id/variables
        """
        return self.api.list_all(host, token, f"projects/{pid}/variables")

    def create_project_variable(self, id, host, token, data, message=None):
        """
        Creates a new project variable

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_level_variables.html#create-variable

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the various data required for creating a project variable. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:id/variables
        """
        if not message:
            message = "Creating project variable"
        return self.api.generate_post_request(host, token, f"projects/{id}/variables", json.dumps(data), description=message)

    def get_all_project_protected_branches(self, id, host, token):
        """
        Gets a list of protected branches from a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_branches.html

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/protected_branches
        """
        return self.api.list_all(host, token, f"projects/{id}/protected_branches")

    def get_single_project_protected_branch(self, pid, name, host, token):
        """
        Gets a single protected branch or wildcard protected branch.

        GitLab API Doc:
            https://docs.gitlab.com/ee/api/protected_branches.html#get-a-single-protected-branch-or-wildcard-protected-branch

            :param: pid: (int) GitLab project ID
            :param: name: (str) GitLab project branch or wildcard name
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/protected_branches/:name
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/protected_branches/{quote_plus(name)}")

    def protect_repository_branches(self, pid, name, host, token, data=None, message=None):
        """
        Protects a single repository branch or several project repository branches using a wildcard protected branch.

        GitLab API Doc:
            https://docs.gitlab.com/ee/api/protected_branches.html#protect-repository-branches

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to PUT /projects/:id/protected_branches
        """
        if not message:
            message = f"Protecting repository branch {name} for project {pid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/protected_branches", data=json.dumps(data), description=message)

    def unprotect_repository_branches(self, pid, name, host, token, message=None):
        """
        Unprotects the given protected branch or wildcard protected branch.

        GitLab API Doc:
            https://docs.gitlab.com/ee/api/protected_branches.html#unprotect-repository-branches

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to PUT /projects/:id/protected_branches/:name
        """
        if not message:
            message = f"Unprotecting repository branch {name} for project {pid}"
        return self.api.generate_delete_request(host, token, f"projects/{pid}/protected_branches/{name}", description=message)

    def set_default_project_branch(self, pid, host, token, branch, data=None, message=None):
        """
        Set default branch for project

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: branch: (str) GitLab project branch name
            :return: Response object containing the response to PUT /projects/:id
        """
        if not message:
            message = f"Setting default branch {branch} for project {pid}"
        return self.api.generate_put_request(host, token, f"projects/{pid}?default_branch={branch}", data=data, description=message)

    def create_branch(self, host, token, pid, data=None, message=None):
        """
        Create branch in project

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to PUT /projects/:id
        """
        if not message:
            message = "Creating branch for project with payload %s" % data
        return self.api.generate_post_request(host, token, f"projects/{pid}/repository/branches", data=data)

    def get_all_project_protected_environments(self, pid, host, token):
        """
        Gets a list of protected environments from a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_environments.html

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/protected_environments
        """
        return self.api.list_all(host, token, f"projects/{pid}/protected_environments")

    def get_all_project_protected_tags(self, pid, host, token):
        """
        Gets a list of protected tags from a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_tags.html#list-protected-tags

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/protected_tags
        """
        return self.api.list_all(host, token, f"projects/{pid}/protected_tags")

    def get_all_project_deploy_keys(self, pid, host, token):
        """
        Get a list of deploy keys for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/deploy_keys.html#list-project-deploy-keys

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/deploy_keys
        """
        return self.api.list_all(host, token, f"projects/{pid}/deploy_keys")

    def get_all_project_jobs(self, id, host, token):
        """
        Get a list of jobs in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/jobs.html#list-project-jobs

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/jobs
        """
        return self.api.list_all(host, token, f"projects/{id}/jobs")

    def get_all_project_pipelines(self, id, host, token):
        """
        Get a list of pipelines in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipelines.html#list-project-pipelines

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/pipelines
        """
        return self.api.list_all(host, token, f"projects/{id}/pipelines")

    def get_all_project_triggers(self, id, host, token):
        """
        Get a list of build triggers for a given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipeline_triggers.html

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/triggers
        """
        return self.api.list_all(host, token, f"projects/{id}/triggers")

    def get_all_project_pipeline_variables(self, prid, piid, host, token):
        """
        Get variables of a given pipeline

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipelines.html

            :param: prid: (int) GitLab project ID
            :param: piid: (int) Pipeline ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/pipelines/:pipeline_id/variables
        """
        return self.api.list_all(host, token, f"projects/{prid}/pipelines/{piid}/variables")

    def get_all_project_pipeline_schedules(self, id, host, token):
        """
        Get a list of the pipeline schedules of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipeline_schedules.html

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/pipeline_schedules
        """
        return self.api.list_all(host, token, f"projects/{id}/pipeline_schedules")

    def get_single_project_pipeline_schedule(self, pid, sid, host, token):
        """
        Get the pipeline schedule of a project.

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipeline_schedules.html

            :param: pid: (int) GitLab project ID
            :param: sid: (int) Schedule ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/pipeline_schedules/:pipeline_schedule_id
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/pipeline_schedules/{sid}")

    def create_new_project_pipeline_schedule(self, host, token, pid, data, message=None):
        """
        Add a hook to a specified project

        GitLab API doc: https://docs.gitlab.com/ee/api/pipeline_schedules.html

            :param: pid: (int) GitLab project ID
            :param: data: (dict) Object containing the various data required for creating a pipeline schedule
            :return: Response object containing the response to POST /projects/:id/pipeline_schedules
        """
        if not message:
            message = "Creating new pipeline schedule"
        return self.api.generate_post_request(host, token, f"projects/{pid}/pipeline_schedules", json.dumps(data), description=message)

    def create_new_project_pipeline_schedule_variable(self, pid, sid, host, token, data, message=None):
        """
        Create a new variable of a pipeline schedule.

        GitLab API doc: https://docs.gitlab.com/ee/api/pipeline_schedules.html

            :param: pid: (int) GitLab project ID
            :param: sid: (int) Schedule ID
            :param: data: (dict) Object containing the various data required for creating a pipeline schedule variable
            :return: Response object containing the response to POST /projects/:id/pipeline_schedules/:pipeline_schedule_id/variables
        """
        if not message:
            message = "Creating new project pipeline schedule variable"
        return self.api.generate_post_request(host, token, f"projects/{pid}/pipeline_schedules/{sid}/variables", json.dumps(data), description=message)

    def get_all_project_hooks(self, pid, host, token):
        """
        Get a list of project hooks

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-project-hooks

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/hooks
        """
        return self.api.list_all(host, token, f"projects/{pid}/hooks")

    def add_project_hook(self, host, token, pid, data, message=None):
        """
        Add a hook to a specified project

        GitLab API doc: https://docs.gitlab.com/ee/api/projects.html#add-project-hook

            :param: pid: (int) GitLab project ID
            :param: data: (dict) Object containing the various data requried for creating a hook. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:id/hooks
        """
        if not message:
            message = "Adding project hook"
        return self.api.generate_post_request(host, token, f"projects/{pid}/hooks", json.dumps(data), description=message)

    def get_all_project_push_rules(self, pid, host, token):
        """
        Get the push rules of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#get-project-push-rules

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/push_rule
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/push_rule")

    def create_project_push_rule(self, pid, host, token, data, message=None):
        """
        Adds a push rule to a specified project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#add-project-push-rule

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (str) Relevant data for creating a push rule
            :return: Response object containing the response to POST /projects/:id/push_rule
        """
        if not message:
            message = "Creating new push rule"
        return self.api.generate_post_request(host, token, f"projects/{pid}/push_rule", json.dumps(data), description=message)

    def get_project_level_mr_approval_configuration(self, pid, host, token):
        """
        Get the approval configuration of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_request_approvals.html#get-configuration

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/approvals
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/approvals")

    def change_project_level_mr_approval_configuration(self, pid, host, token, data, message=None):
        """
        Change the approval configuration of a project

         GitLab API Doc: https://docs.gitlab.com/ee/api/merge_request_approvals.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (str) Relevant data for approval configuration
            :return: Response object containing the response to PUT /projects/:id/approvals
        """
        if not message:
            message = "Changing project merge request approval"
        return self.api.generate_post_request(host, token, f"projects/{pid}/approvals", json.dumps(data), description=message)

    def get_all_project_level_mr_approval_rules(self, pid, host, token):
        """
        Get the approval rules of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_request_approvals.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/approval_rules
        """
        return self.api.list_all(host, token, f"projects/{pid}/approval_rules")

    def create_project_level_mr_approval_rule(self, pid, host, token, data, message=None):
        """
        Create project-level rule

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_request_approvals.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (str) Relevant data for approval rule
            :yield: Generator returning JSON of each result from POST /projects/:id/approval_rules
        """
        if not message:
            message = f"Creating project level merge request approval rule with payload {data}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/approval_rules", json.dumps(data), description=message)

    def get_all_project_registry_repositories(self, pid, host, token):
        """
        Get a list of registry repositories in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/container_registry.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/registry/repositories
        """
        return self.api.list_all(host, token, f"projects/{pid}/registry/repositories")

    def get_all_project_registry_repositories_tags(self, pid, rid, host, token):
        """
        Get a list of tags for given registry repository

        GitLab API Doc: https://docs.gitlab.com/ee/api/container_registry.html

            :param: pid: (int) GitLab project ID
            :param: rid: (int) Repository ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/registry/repositories/:repository_id/tags
        """
        return self.api.list_all(host, token, f"projects/{pid}/registry/repositories/{rid}/tags")

    def get_project_registry_repository_tag_details(self, pid, rid, tag_name, host, token):
        """
        Get a list of tags for given registry repository

        GitLab API Doc: https://docs.gitlab.com/ee/api/container_registry.html

            :param: pid: (int) GitLab project ID
            :param: rid: (int) Repository ID
            :param: tag_name: (int) Tag name
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:id/registry/repositories/:repository_id/tags/:tag_name
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/registry/repositories/{rid}/tags/{tag_name}")

    def get_all_project_feature_flags(self, id, host, token):
        """
        Gets all feature flags of the requested project

        GitLab API Doc: https://docs.gitlab.com/ee/api/feature_flags.html

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/feature_flags
        """
        return self.api.list_all(host, token, f"projects/{id}/feature_flags")

    def get_all_project_custom_attributes(self, id, host, token):
        """
        Get all custom attributes on a resource

        GitLab API Doc: https://docs.gitlab.com/ee/api/custom_attributes.html

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/custom_attributes
        """
        return self.api.list_all(host, token, f"projects/{id}/custom_attributes")

    def get_all_project_snippets(self, pid, host, token):
        """
        Get a list of project snippets

        GitLab API Doc: https://docs.gitlab.com/ee/api/notes.html#list-project-issue-notes

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/snippets
        """
        return self.api.list_all(host, token, f"projects/{pid}/snippets")

    def get_single_project_snippets(self, host, token, project_id, snippet_id):
        """
        Get a single project snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_snippets.html#single-snippet

            :param: project_id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:id/snippets/:snippet_id
        """
        return self.api.generate_get_request(host, token, f"projects/{project_id}/snippets/{snippet_id}")

    def get_project_snippet_awards(self, host, token, project_id, snippet_id):
        """
        Get a list of all award emoji for a specified project snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html

            :param: project_id: (int) GitLab group ID
            :param: snippet_id: (int) Snipped ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/snippets/:snippet_id/award_emoji
        """
        return self.api.generate_get_request(host, token, f"projects/{project_id}/snippets/{snippet_id}/award_emoji")

    def create_project_snippet_award(self, host, token, project_id, snippet_id, name):
        """
        Create an award emoji on the specified project snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#award-a-new-emoji

            :param: project_id: (int) GitLab project ID
            :param: snippet_id: (int) Snipped ID
            :param: name: (int) Name of the award
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/snippets/:snippet_id/award_emoji
        """
        return self.api.generate_post_request(host, token, f"projects/{project_id}/snippets/{snippet_id}/award_emoji?name={name}", None)

    def get_project_snippet_note_awards(self, host, token, project_id, snippet_id, note_id):
        """
        Get all award emoji for an snippet note

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html

            :param: project_id: (int) GitLab group ID
            :param: snippet_id: (int) Snipped ID
            :param: note_id: (int) Note ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/snippets/:snippet_id/notes/:note_id/award_emoji
        """
        return self.api.generate_get_request(host, token, f"projects/{project_id}/snippets/{snippet_id}/notes/{note_id}/award_emoji")

    def create_project_snippet_note_award(self, host, token, project_id, snippet_id, note_id, name):
        """
        Create an award emoji on the specified project snippet note

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html

            :param: project_id: (int) GitLab project ID
            :param: snippet_id: (int) Snipped ID
            :param: note_id: (int) Note ID
            :param: name: (int) Name of the award
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/snippets/:snippet_id/notes/:note_id/award_emoji
        """
        return self.api.generate_post_request(host, token, f"projects/{project_id}/snippets/{snippet_id}/notes/{note_id}/award_emoji?name={name}", None)

    def get_project_snippet_notes(self, host, token, project_id, snippet_id):
        """
        Gets a list of all notes for a single snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/notes.html#list-all-snippet-notes

            :param: project_id: (int) GitLab group ID
            :param: snippet_id: (int) Snipped ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/snippets/:snippet_id/notes
        """
        return self.api.generate_get_request(host, token, f"projects/{project_id}/snippets/{snippet_id}/notes")

    def get_environment(self, project_id, env_id, host, token):
        """
        Get a specific environment

        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html

            :param: project_id: (int) GitLab project ID
            :param: env_id: (int) GitLab project environment ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/:id/environments/:environment_id

        """
        return self.api.generate_get_request(host, token, f"projects/{project_id}/environments/{env_id}")

    def get_all_project_environments(self, pid, host, token):
        """
        Get all project environments

        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: RGenerator returning JSON of each result from GET /projects/:id/environments

        """
        return self.api.list_all(host, token, f"projects/{pid}/environments")

    def get_all_project_wikis(self, pid, host, token):
        """
        Get all project wikis

        GitLab API Doc: https://docs.gitlab.com/ee/api/wikis.html#list-wiki-pages

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: RGenerator returning JSON of each result from GET /projects/:id/wikis

        """
        return self.api.list_all(host, token, f"projects/{pid}/wikis")

    def create_environment(self, host, token, project_id, data, message=None):
        """
        Creates a new environment

        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: project_id: (str) GitLab project ID
            :param: data: (dict) Object containing the necessary data for creating an environment. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:id/environments

        """
        if not message:
            message = "Creating new environment with payload %s" % str(data)
        return self.api.generate_post_request(host, token, f"projects/{project_id}/environments", json.dumps(data), description=message)

    def delete_environment(self, project_id, env_id, host, token):
        """
        Delete a project environment

        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html#delete-an-environment

            :param: project_id: (int) GitLab project ID
            :param: env_id: (int) GitLab project environment ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 204 (No Content) or 404 (Group not found) from DELETE /projects/:id/environments/:environment_id
        """
        return self.api.generate_delete_request(host, token, f"projects/{project_id}/environments/{env_id}")

    def get_project_statistics(self, project_full_path, host, token):
        query = {
            "query": """
                query {
                    project(fullPath: "%s") {
                        importStatus,
                        statistics {
                                commitCount,
                                repositorySize,
                                lfsObjectsSize,
                                storageSize
                            }
                        }
                }
            """ % project_full_path
        }

        return self.api.generate_post_request(host, token, None, json.dumps(query), graphql_query=True)

    def get_all_project_clusters(self, pid, host, token):
        """
        Returns a list of project clusters.

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_clusters.html#list-project-clusters

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/:id/clusters

        """
        return self.api.list_all(host, token, f"projects/{pid}/clusters")

    def add_project_cluster(self, pid, host, token, data=None, message=None):
        """
        Adds an existing Kubernetes cluster to the project.

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_clusters.html#add-existing-cluster-to-project

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the necessary data for the added cluster
            :return: Response object containing the response to POST /projects/:id/clusters/user

        """
        if not message:
            message = f"Adding cluster {data['name']} to project {pid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/clusters/user", json.dumps(data), description=message)

    def enable_deploy_key(self, pid, kid, host, token, message=None):
        """
        Enables a deploy key for a project so this can be used. Returns the enabled key, with a status code 201 when successful.

        GitLab API Doc: https://docs.gitlab.com/ee/api/deploy_keys.html#enable-a-deploy-key

            :param: pid: (int) GitLab project ID
            :param: kid: (int) The ID of the deploy key
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:pid/deploy_keys/:kid/enable

        """
        if not message:
            message = (f"Enabling deploy key {kid} for project {pid}")
        return self.api.generate_post_request(host, token, f"projects/{pid}/deploy_keys/{kid}/enable", {}, description=message)
