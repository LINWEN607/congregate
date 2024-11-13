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
            :return: Response object containing the response to GET /projects/:pid

        """
        return self.api.generate_get_request(host, token, f"projects/{pid}")

    def get_project_by_path_with_namespace(self, path, host, token):
        """
        Get all details of a project matching the path_with_namespace

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#get-single-project

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
        return self.api.list_all(host, token, f"projects{'?statistics=true' if statistics else ''}", keyset=False)

    def get_members(self, pid, host, token):
        """
        Gets a list of group or project members viewable by the authenticated user

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator containing JSON results from GET /projects

        """
        for member in self.api.list_all(host, token, f"projects/{pid}/members"):
            member["email"] = self.users.get_user_email(
                member["id"], host, token)
            yield member

    def get_members_incl_inherited(self, pid, host, token):
        """
        Gets a list of project members viewable by the authenticated user, including inherited members through ancestor groups

        GitLab API Doc: GitLab API Doc: https://docs.gitlab.com/ee/api/members.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/members/all
        """
        for member in self.api.list_all(host, token, f"projects/{pid}/members/all"):
            member["email"] = self.users.get_user_email(
                member["id"], host, token)
            yield member

    def edit_member(self, host, token, pid, mid, level, message=None):
        """
        Updates the access_level of a project member.

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#edit-a-member-of-a-group-or-project

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: pid: (int) GitLab project ID
            :param: mid: (int) GitLab project member ID
            :param: level: (int) GitLab project member access level
            :yield: Response object containing the response to PUT /projects/:pid/members/:mid
        """
        return self.api.generate_put_request(host, token, f"projects/{pid}/members/{mid}?access_level={level}", data=None, description=message)

    def add_member(self, pid, host, token, member, message=None):
        """
        Adds a member to a group or project

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: member: (dict) Object containing the member data. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:pid/members

        """
        if not message:
            message = f"Adding user {member['user_id']} to project {pid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/members", json.dumps(member), description=message)

    def remove_member(self, pid, uid, host, token, message=None):
        """
        Removes member from project

        GitLab API Doc: https://docs.gitlab.com/ee/api/members.html

            :param: pid: (int) GitLab project ID
            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 202 (accepted) or 404 (Member not found) from DELETE /projects/:pid/members/:uid
        """
        if not message:
            message = "Deleting member from project"
        return self.api.generate_delete_request(host, token, f"projects/{pid}/members/{uid}", description=message)

    def create_new_project_deploy_key(self, pid, host, token, key, message=None):
        """
        Creates a new deploy key for a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/deploy_keys.html#add-deploy-key

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: key: (dict) Object containing the key data. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:pid/deploy_keys

        """
        if not message:
            message = "Creating new deploy key"
        return self.api.generate_post_request(host, token, f"projects/{pid}/deploy_keys", json.dumps(key), description=message)

    def archive_project(self, host, token, pid, message=None):
        """
        Archives the project if the user is either admin or the project owner of this project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#archive-a-project

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:pid/archive

        """
        if not message:
            message = f"Archiving project {pid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/archive", {}, description=message)

    def unarchive_project(self, host, token, pid, message=None):
        """
        Unarchives the project if the user is either admin or the project owner of this project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#unarchive-a-project

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:pid/unarchive

        """
        if not message:
            message = f"Unarchiving project {pid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/unarchive", {}, description=message)

    def get_project_archive_state(self, host, token, pid):
        """
        Retrieves the archive state of the project.

            :param pid: (int) GitLab project ID
            :param host: (str) GitLab host URL
            :param token: (str) Access token to GitLab instance
            :return: Boolean indicating if the project is archived
        """
        response = self.get_project(pid, host, token)
        if response.status_code == 200:
            project_data = response.json()
            return project_data.get("archived", True)
        response.raise_for_status()
        return True

    def delete_project(self, host, token, pid, full_path=None, permanent=False):
        """
        Removes a project including all associated resources

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#remove-project

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing a 202 (Accepted) or 404 (Project not found) from DELETE /projects/:pid
        """
        message = f"Deleting destination project {pid})"
        if permanent and full_path:
            message += f" '{full_path}' permanently"
            return self.api.generate_delete_request(host, token, f"projects/{pid}?&full_path={quote_plus(full_path)}&permanently_remove=true", description=message)
        return self.api.generate_delete_request(host, token, f"projects/{pid}", description=message)

    def add_shared_group(self, host, token, pid, data=None, message=None):
        """
        Allow to share project with group

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#share-project-with-group

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: group: (dict) Object containing the necessary data for the shared group
            :return: Response object containing the response to POST /projects/:pid/share

        """
        if not message:
            message = f"Sharing project {pid} with group {data['group_id']}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/share", json.dumps(data), description=message)

    def edit_project(self, host, token, pid, data=None, message=None):
        """
        Edit a project

        GitLab API doc: https://docs.gitlab.com/ee/api/projects.html#edit-project

            :param: pid: (int) GitLab project ID
            :return: Response object containing the response to PUT /projects/:pid
        """
        if not message:
            audit_data = data.copy()
            audit_data.pop("import_url", None)
            message = f"Editing project {pid} with payload {str(audit_data)}"
        return self.api.generate_put_request(host, token, f"projects/{pid}", json.dumps(data), description=message)

    def start_pull_mirror(self, host, token, pid, data=None):
        """
        Start the pull mirroring process for a Project

        GitLab API doc: https://docs.gitlab.com/ee/api/project_pull_mirroring.html#start-the-pull-mirroring-process-for-a-project

            :param: pid: (int) GitLab project ID
            :return: Response object containing the response to PUT /projects/:pid/mirror/pull
        """
        return self.api.generate_post_request(host, token, f"projects/{pid}/mirror/pull", json.dumps(data))

    def create_project(self, host, token, name, data=None, headers=None, message=None):
        """
        Creates a new project owned by the authenticated user.

        GitLab API doc: https://docs.gitlab.com/ee/api/projects.html#create-project

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: name: (str) GitLab project name
            :return: Response object containing the response to POST /projects
        """
        if data is not None:
            data["name"] = name
        else:
            data = {"name": name}
        if not message:
            message = f"Creating project {name} with payload {str(data)}"
        return self.api.generate_post_request(host, token, "projects", json.dumps(data), headers=headers, description=message)

    def export_project(self, host, token, pid, data=None, headers=None, message=None):
        """
        Schedule an export

        GitLab API doc: https://docs.gitlab.com/ee/api/project_import_export.html#schedule-an-export

            :param: pid: (int) GitLab project ID
            :return: Response object containing the response to POST /projects/:pid/export
        """
        if not message:
            message = f"Exporting project {pid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/export", data, headers=headers, description=message)

    def get_project_export_status(self, pid, host, token):
        """
        Get the status of export

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_import_export.html#export-status

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:pid/export
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/export")

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
            message = f"Importing project with payload {str(data)}"
        return self.api.generate_post_request(host, token, "projects/import", data, files=files, headers=headers, description=message)

    def get_project_import_status(self, host, token, pid):
        """
        Get the status of an import

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_import_export.html#import-status

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:pid/import
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/import")

    def get_all_project_users(self, pid, host, token):
        """
        Get the users list of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#get-project-users

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/users
        """
        return self.api.list_all(host, token, f"projects/{pid}/users")

    def get_all_project_forks(self, pid, host, token):
        """
        List the projects accessible to the calling user that have an established, forked relationship with the specified project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-forks-of-a-project

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/forks
        """
        return self.api.list_all(host, token, f"projects/{pid}/forks")

    def create_project_fork_relation(self, fpid, pid, host, token, message=None):
        """
        Create a forked from/to relation between existing projects

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#create-a-forked-fromto-relation-between-existing-projects

            :param: fpid: (int) GitLab fork project ID
            :param: pid: (int) GitLab forked from project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:fpid/fork/:pid
        """
        if not message:
            message = f"Creating forked from {pid} to {fpid} project relation"
        return self.api.generate_post_request(host, token, f"projects/{fpid}/fork/{pid}", data=None, description=message)

    def get_all_project_starrers(self, pid, host, token):
        """
        List the users who starred the specified project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-starrers-of-a-project

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/starrers
        """
        return self.api.list_all(host, token, f"projects/{pid}/starrers")

    def get_all_project_badges(self, pid, host, token):
        """
        Gets a list of a project badges and its group badges

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_badges.html#project-badges-api

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/badges
        """
        return self.api.list_all(host, token, f"projects/{pid}/badges")

    def get_all_project_boards(self, pid, host, token):
        """
        Lists Issue Boards in the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/boards.html#project-board

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/boards
        """
        return self.api.list_all(host, token, f"projects/{pid}/boards")

    def get_all_project_labels(self, pid, host, token):
        """
        Get all labels for a given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/labels.html#list-labels

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/labels
        """
        return self.api.list_all(host, token, f"projects/{pid}/labels?include_ancestor_groups=false")

    def get_all_project_milestones(self, pid, host, token):
        """
        Returns a list of project milestones

        GitLab API Doc: https://docs.gitlab.com/ee/api/milestones.html#list-project-milestones

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/milestones
        """
        return self.api.list_all(host, token, f"projects/{pid}/milestones")

    def get_all_project_issues(self, pid, host, token):
        """
        Returns a list of project issues

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-project-issues

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/issues
        """
        return self.api.list_all(host, token, f"projects/{pid}/issues")

    def get_all_project_releases(self, pid, host, token):
        """
        Returns a paginated list releases for a given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/releases/#list-releases

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/releases
        """
        return self.api.list_all(host, token, f"projects/{pid}/releases")

    def get_all_project_events(self, pid, host, token):
        """
        Get a list of visible events for a particular project

        GitLab API Doc: https://docs.gitlab.com/ee/api/events.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/events
        """
        return self.api.list_all(host, token, f"projects/{pid}/events")

    def get_all_project_variables(self, pid, host, token):
        """
        Get list of variables for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_level_variables.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:pid/variables
        """
        return self.api.list_all(host, token, f"projects/{pid}/variables")

    def create_project_variable(self, pid, host, token, data, message=None):
        """
        Creates a new project variable

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_level_variables.html#create-variable

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the various data required for creating a project variable. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:pid/variables
        """
        if not message:
            message = f"Creating project {pid} variable"
        return self.api.generate_post_request(host, token, f"projects/{pid}/variables", json.dumps(data), description=message)

    def get_all_project_protected_branches(self, pid, host, token):
        """
        Gets a list of protected branches from a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_branches.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/protected_branches
        """
        return self.api.list_all(host, token, f"projects/{pid}/protected_branches")

    def get_single_project_protected_branch(self, pid, name, host, token):
        """
        Gets a single protected branch or wildcard protected branch.

        GitLab API Doc:
            https://docs.gitlab.com/ee/api/protected_branches.html#get-a-single-protected-branch-or-wildcard-protected-branch

            :param: pid: (int) GitLab project ID
            :param: name: (str) GitLab project branch or wildcard name
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/protected_branches/:name
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/protected_branches/{quote_plus(name)}")

    def protect_repository_branches(self, pid, name, host, token, data=None, message=None):
        """
        Protects a single repository branch or several project repository branches using a wildcard protected branch.

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_branches.html#protect-repository-branches

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to PUT /projects/:pid/protected_branches
        """
        if not message:
            message = f"Protecting repository branch {name} for project {pid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/protected_branches", json.dumps(data), description=message)

    def unprotect_repository_branches(self, pid, name, host, token, message=None):
        """
        Unprotects the given protected branch or wildcard protected branch.

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_branches.html#unprotect-repository-branches

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to PUT /projects/:pid/protected_branches/:name
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
            :return: Response object containing the response to PUT /projects/:pid
        """
        if not message:
            message = f"Setting default branch {branch} for project {pid}"
        return self.api.generate_put_request(host, token, f"projects/{pid}?default_branch={branch}", data, description=message)

    def create_branch(self, host, token, pid, data=None, message=None):
        """
        Create a new branch in the repository.

        GitLab API Doc: https://docs.gitlab.com/ee/api/branches.html#create-repository-branch

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to PUT /projects/:pid
        """
        if not message:
            message = f"Creating branch for project {pid} with payload {data}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/repository/branches", json.dumps(data))

    def delete_branch(self, host, token, pid, branch, message=None):
        """
        Delete a branch from the repository.

        GitLab API Doc: https://docs.gitlab.com/ee/api/branches.html#delete-repository-branch

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: branch: (str) Name of the branch
            :return: Response object containing the response to DELETE /projects/:pid/repository/branches/:branch
        """
        if not message:
            message = f"Deleting project {pid} branch {branch}"
        return self.api.generate_delete_request(host, token, f"projects/{pid}/repository/branches/{branch}")

    def get_all_project_protected_environments(self, pid, host, token):
        """
        Gets a list of protected environments from a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_environments.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/protected_environments
        """
        return self.api.list_all(host, token, f"projects/{pid}/protected_environments")

    def get_all_project_protected_tags(self, pid, host, token):
        """
        Gets a list of protected tags from a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_tags.html#list-protected-tags

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/protected_tags
        """
        return self.api.list_all(host, token, f"projects/{pid}/protected_tags")

    def get_all_project_deploy_keys(self, pid, host, token):
        """
        Get a list of deploy keys for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/deploy_keys.html#list-project-deploy-keys

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/deploy_keys
        """
        return self.api.list_all(host, token, f"projects/{pid}/deploy_keys")

    def get_all_project_jobs(self, pid, host, token):
        """
        Get a list of jobs in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/jobs.html#list-project-jobs

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/jobs
        """
        return self.api.list_all(host, token, f"projects/{pid}/jobs")

    def get_all_project_pipelines(self, pid, host, token):
        """
        Get a list of pipelines in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipelines.html#list-project-pipelines

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/pipelines
        """
        return self.api.list_all(host, token, f"projects/{pid}/pipelines")

    def get_all_project_triggers(self, pid, host, token):
        """
        Get a list of build triggers for a given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipeline_triggers.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/triggers
        """
        return self.api.list_all(host, token, f"projects/{pid}/triggers")

    def get_all_project_pipeline_variables(self, prid, piid, host, token):
        """
        Get variables of a given pipeline

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipelines.html

            :param: prid: (int) GitLab project ID
            :param: piid: (int) Pipeline ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:prid/pipelines/:piid/variables
        """
        return self.api.list_all(host, token, f"projects/{prid}/pipelines/{piid}/variables")

    def get_all_project_pipeline_schedules(self, pid, host, token):
        """
        Get a list of the pipeline schedules of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipeline_schedules.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/pipeline_schedules
        """
        return self.api.list_all(host, token, f"projects/{pid}/pipeline_schedules")

    def get_single_project_pipeline_schedule(self, pid, psid, host, token):
        """
        Get the pipeline schedule of a project.

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipeline_schedules.html

            :param: pid: (int) GitLab project ID
            :param: psid: (int) GitLab pipeline schedule ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/pipeline_schedules/:psid
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/pipeline_schedules/{psid}")

    def create_new_project_pipeline_schedule(self, host, token, pid, data, message=None):
        """
        Add a hook to a specified project

        GitLab API doc: https://docs.gitlab.com/ee/api/pipeline_schedules.html

            :param: pid: (int) GitLab project ID
            :param: data: (dict) Object containing the various data required for creating a pipeline schedule
            :return: Response object containing the response to POST /projects/:pid/pipeline_schedules
        """
        if not message:
            message = f"Creating new pipeline schedule for project {pid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/pipeline_schedules", json.dumps(data), description=message)

    def create_new_project_pipeline_schedule_variable(self, pid, psid, host, token, data, message=None):
        """
        Create a new variable of a pipeline schedule.

        GitLab API doc: https://docs.gitlab.com/ee/api/pipeline_schedules.html

            :param: pid: (int) GitLab project ID
            :param: psid: (int) GitLab pipeline schedule ID
            :param: data: (dict) Object containing the various data required for creating a pipeline schedule variable
            :return: Response object containing the response to POST /projects/:pid/pipeline_schedules/:psid/variables
        """
        if not message:
            message = f"Creating project {pid} new pipeline schedule variable {psid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/pipeline_schedules/{psid}/variables", json.dumps(data), description=message)

    def get_all_project_hooks(self, pid, host, token):
        """
        Get a list of project hooks

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-project-hooks

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/hooks
        """
        return self.api.list_all(host, token, f"projects/{pid}/hooks")

    def add_project_hook(self, host, token, pid, data, message=None):
        """
        Add a hook to a specified project

        GitLab API doc: https://docs.gitlab.com/ee/api/projects.html#add-project-hook

            :param: pid: (int) GitLab project ID
            :param: data: (dict) Object containing the various data required for creating a hook. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:pid/hooks
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
            :yield: Generator returning JSON of each result from GET /projects/:pid/push_rule
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
            :return: Response object containing the response to POST /projects/:pid/push_rule
        """
        if not message:
            message = f"Creating new push rule for project {pid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/push_rule", json.dumps(data), description=message)

    def get_project_level_mr_approval_configuration(self, pid, host, token):
        """
        Get the approval configuration of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_request_approvals.html#get-configuration

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/approvals
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
            :return: Response object containing the response to PUT /projects/:pid/approvals
        """
        if not message:
            message = f"Changing project {pid} merge request approval"
        return self.api.generate_post_request(host, token, f"projects/{pid}/approvals", json.dumps(data), description=message)

    def get_all_project_level_mr_approval_rules(self, pid, host, token):
        """
        Get the approval rules of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_request_approvals.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/approval_rules
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
            :yield: Generator returning JSON of each result from POST /projects/:pid/approval_rules
        """
        if not message:
            message = f"Creating project {pid} level merge request approval rule with payload {data}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/approval_rules", json.dumps(data), description=message)

    def get_all_project_registry_repositories(self, pid, host, token):
        """
        Get a list of registry repositories in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/container_registry.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/registry/repositories
        """
        return self.api.list_all(host, token, f"projects/{pid}/registry/repositories")

    def get_all_project_registry_repositories_tags(self, pid, rid, host, token):
        """
        Get a list of tags for given registry repository

        GitLab API Doc: https://docs.gitlab.com/ee/api/container_registry.html

            :param: pid: (int) GitLab project ID
            :param: rid: (int) GitLab repository ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/registry/repositories/:rid/tags
        """
        return self.api.list_all(host, token, f"projects/{pid}/registry/repositories/{rid}/tags")

    def get_project_registry_repository_tag_details(self, pid, rid, tag_name, host, token):
        """
        Get a list of tags for given registry repository

        GitLab API Doc: https://docs.gitlab.com/ee/api/container_registry.html

            :param: pid: (int) GitLab project ID
            :param: rid: (int) GitLab repository ID
            :param: tag_name: (int) Tag name
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:pid/registry/repositories/:rid/tags/:tag_name
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/registry/repositories/{rid}/tags/{tag_name}")

    def get_all_project_feature_flags(self, pid, host, token):
        """
        Gets all feature flags of the requested project

        GitLab API Doc: https://docs.gitlab.com/ee/api/feature_flags.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/feature_flags
        """
        return self.api.list_all(host, token, f"projects/{pid}/feature_flags")

    def get_all_project_custom_attributes(self, pid, host, token):
        """
        Get all custom attributes on a resource

        GitLab API Doc: https://docs.gitlab.com/ee/api/custom_attributes.html

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/custom_attributes
        """
        return self.api.list_all(host, token, f"projects/{pid}/custom_attributes")

    def get_all_project_snippets(self, pid, host, token):
        """
        Get a list of project snippets

        GitLab API Doc: https://docs.gitlab.com/ee/api/notes.html#list-project-issue-notes

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/snippets
        """
        return self.api.list_all(host, token, f"projects/{pid}/snippets")

    def get_single_project_snippets(self, host, token, pid, sid):
        """
        Get a single project snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_snippets.html#single-snippet

            :param: pid: (int) GitLab project ID
            :param: sid: (int) GitLab snippet ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:pid/snippets/:sid
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/snippets/{sid}")

    def get_project_snippet_awards(self, host, token, pid, sid):
        """
        Get a list of all award emoji for a specified project snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html

            :param: pid: (int) GitLab project ID
            :param: sid: (int) GitLab snippet ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/snippets/:sid/award_emoji
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/snippets/{sid}/award_emoji")

    def create_project_snippet_award(self, host, token, pid, sid, name):
        """
        Create an award emoji on the specified project snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#award-a-new-emoji

            :param: pid: (int) GitLab project ID
            :param: sid: (int) GitLab snippet ID
            :param: name: (int) Name of the award
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:pid/snippets/:sid/award_emoji
        """
        return self.api.generate_post_request(host, token, f"projects/{pid}/snippets/{sid}/award_emoji?name={name}", None)

    def get_project_snippet_note_awards(self, host, token, pid, sid, nid):
        """
        Get all award emoji for an snippet note

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html

            :param: pid: (int) GitLab project ID
            :param: sid: (int) GitLab snippet ID
            :param: nid: (int) GitLag note ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/snippets/:sid/notes/:nid/award_emoji
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/snippets/{sid}/notes/{nid}/award_emoji")

    def create_project_snippet_note_award(self, host, token, pid, sid, nid, name):
        """
        Create an award emoji on the specified project snippet note

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html

            :param: pid: (int) GitLab project ID
            :param: sid: (int) GitLab snippet ID
            :param: nid: (int) GitLab note ID
            :param: name: (int) Name of the award
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:pid/snippets/:sid/notes/:nid/award_emoji
        """
        return self.api.generate_post_request(host, token, f"projects/{pid}/snippets/{sid}/notes/{nid}/award_emoji?name={name}", None)

    def get_project_snippet_notes(self, host, token, pid, sid):
        """
        Gets a list of all notes for a single snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/notes.html#list-all-snippet-notes

            :param: pid: (int) GitLab project ID
            :param: sid: (int) GitLab snippet ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/snippets/:sid/notes
        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/snippets/{sid}/notes")

    def get_environment(self, pid, eid, host, token):
        """
        Get a specific environment

        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html

            :param: pid: (int) GitLab project ID
            :param: eid: (int) GitLab project environment ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/:pid/environments/:eid

        """
        return self.api.generate_get_request(host, token, f"projects/{pid}/environments/{eid}")

    def get_all_project_wikis(self, pid, host, token):
        """
        Get all project wikis

        GitLab API Doc: https://docs.gitlab.com/ee/api/wikis.html#list-wiki-pages

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/wikis

        """
        return self.api.list_all(host, token, f"projects/{pid}/wikis")

    def get_all_project_environments(self, pid, host, token):
        """
        Get all project environments

        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html#list-environments

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:pid/environments

        """
        return self.api.list_all(host, token, f"projects/{pid}/environments")

    def create_environment(self, host, token, pid, data, message=None):
        """
        Creates a new environment

        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html#create-a-new-environment

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: pid: (str) GitLab project ID
            :param: data: (dict) Object containing the necessary data for creating an environment. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:pid/environments

        """
        if not message:
            message = f"Creating new environment for project {pid} with payload {str(data)}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/environments", json.dumps(data), description=message)

    def create_protected_environment(self, host, token, pid, data, message=None):
        """
        Creates a new protected environment

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_environments.html#protect-a-single-environment

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: pid: (str) GitLab project ID
            :param: data: (dict) Object containing the necessary data for creating an environment. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:pid/protected_environments

        """
        if not message:
            message = f"Creating new protected environment for project {pid} with payload {json.dumps(data)}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/protected_environments", json.dumps(data), description=message)

    def update_protected_environment(self, host, token, pid, data, name, message=None):
        """
        Creates a new protected environment

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_environments.html#protect-a-single-environment

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: pid: (str) GitLab project ID
            :param: data: (dict) Object containing the necessary data for creating an environment. Refer to the link above for specific examples
            :param: name: (str) The name of the environment
            :return: Response object containing the response to POST /projects/:pid/protected_environments

        """
        if not message:
            message = f"Updating protected environment {name} for project {pid} with payload {str(data)}"
        return self.api.generate_put_request(host, token, f"projects/{pid}/protected_environments/{name}", json.dumps(data), description=message)

    def unprotect_environment(self, host, token, pid, name, message=None):
        """
        unprotect an environment.

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_environments.html#unprotect-a-single-environment

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: pid: (int) GitLab project ID
            :param: name: (str) The name of the environment
            :return: Response object containing the response to DELETE /projects/:pid/protected_environments/:name

        """
        if not message:
            message = f"Unprotecting environment {name} for project {pid}"
        return self.api.generate_delete_request(host, token, f"projects/{pid}/protected_environments/{name}")

    def stop_environment(self, host, token, pid, eid, data, message=None):
        """
        It returns 200 if the environment was successfully stopped, and 404 if the environment does not exist.

        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html#stop-an-environment

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: pid: (int/str) GitLab project ID
            :param: eid: (int) The ID of the environment.
            :return: Response object containing the response to POST /projects/:pid/environments/:eid/stop

        """
        if not message:
            message = f"Stopping environment {eid} for project {pid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/environments/{eid}/stop", json.dumps(data), description=message)

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
                        repository {
                                empty
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
            :return: Response object containing the response to GET /projects/:pid/clusters

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
            :return: Response object containing the response to POST /projects/:pid/clusters/user

        """
        if not message:
            message = f"Adding cluster {data['name']} to project {pid}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/clusters/user", json.dumps(data), description=message)

    def enable_deploy_key(self, pid, kid, host, token, message=None):
        """
        Enables a deploy key for a project so this can be used. Returns the enabled key, with a status code 201 when successful.

        GitLab API Doc: https://docs.gitlab.com/ee/api/deploy_keys.html#enable-a-deploy-key

            :param: pid: (int) GitLab project ID
            :param: kid: (int) GitLab deploy key ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:pid/deploy_keys/:kid/enable

        """
        if not message:
            message = (f"Enabling deploy key {kid} for project {pid}")
        return self.api.generate_post_request(host, token, f"projects/{pid}/deploy_keys/{kid}/enable", {}, description=message)

    def create_remote_push_mirror(self, pid, host, token, data=None, message=None):
        """
        Create a remote mirror for a project. The mirror is disabled by default

        GitLab API Doc: https://docs.gitlab.com/ee/api/remote_mirrors.html#create-a-remote-mirror

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab mirrored repo URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the necessary data for remote mirror
            :return: Response object containing the response to POST /projects/:id/remote_mirrors
        """
        if not message:
            audit_data = data.copy()
            audit_data.pop("url")
            message = (
                f"Creating project {pid} remote mirror with payload {audit_data}")
        return self.api.generate_post_request(host, token, f"projects/{pid}/remote_mirrors", json.dumps(data), description=message)

    def get_all_remote_push_mirrors(self, pid, host, token):
        """
        Returns an Array of remote mirrors and their statuses

        GitLab API Doc: https://docs.gitlab.com/ee/api/remote_mirrors.html#list-a-projects-remote-mirrors

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab mirrored repo URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/:pid/remote_mirrors
        """
        return self.api.list_all(host, token, f"projects/{pid}/remote_mirrors")

    def edit_remote_push_mirror(self, pid, mid, host, token, data=None, message=None):
        """
        Toggle a remote mirror on or off, or change which types of branches are mirrored

        GitLab API doc: https://docs.gitlab.com/ee/api/remote_mirrors.html#update-a-remote-mirrors-attributes

            :param: pid: (int) GitLab project ID
            :param: mid: (int) GitLab project mirror ID
            :param: host: (str) GitLab mirrored repo URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the necessary data for remote mirror
            :return: Response object containing the response to PUT /projects/:pid/remote_mirrors/:mid
        """
        if not message:
            message = f"Editing project {pid} remote push mirror {mid} with payload {str(data)}"
        return self.api.generate_put_request(host, token, f"projects/{pid}/remote_mirrors/{mid}", json.dumps(data), description=message)

    def delete_remote_push_mirror(self, host, token, pid, mid, message=None):
        """
        Delete a remote mirror.

        GitLab API Doc: https://docs.gitlab.com/ee/api/remote_mirrors.html#delete-a-remote-mirror

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: pid: (int) GitLab project ID
            :param: mid: (ind) Remote mirror ID
            :return: Response object containing the response to DELETE /projects/:pid/remote_mirrors/:mid
        """
        if not message:
            message = f"Deleting project {pid} remote push mirror {mid}"
        return self.api.generate_delete_request(host, token, f"projects/{pid}/remote_mirrors/{mid}")

    def create_project_access_token(self, pid, host, token, data, message=None):
        """
        Create a project access token.

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_access_tokens.html#create-a-project-access-token

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the various data required for creating a project access token.
                Refer to the link above for specific examples.
            :return: Response object containing the response to POST projects/:id/access_tokens
        """
        if not message:
            message = f"Creating project access token with payload {str(data)}"
        return self.api.generate_post_request(host, token, f"projects/{pid}/access_tokens", json.dumps(data), description=message)

    def get_project_repository_commits(self, pid, host, token):
        return self.api.list_all(host, token, f"projects/{pid}/repository/commits")

    def get_project_repository_commit_comments(self, pid, sha, host, token):
        return self.api.list_all(host, token, f"projects/{pid}/repository/commits/{sha}/comments")
