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

    def create_new_project_deploy_key(self, id, host, token, key):
        """
        Creates a new deploy key for a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/deploy_keys.html#add-deploy-key

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: key: (dict) Object containing the key data. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:id/deploy_keys

        """
        return api.generate_post_request(host, token, "projects/%d/deploy_keys" % id, json.dumps(key))

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

        GitLab API Doc: GitLab API Doc: https://docs.gitlab.com/ee/api/members.html#list-all-members-of-a-group-or-project-including-inherited-members

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/members/all
        """
        return api.list_all(host, token, "projects/%d/members/all" % id)

    def get_all_project_starrers(self, id, host, token):
        """
        List the users who starred the specified project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-starrers-of-a-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/starrers
        """
        return api.list_all(host, token, "projects/%d/starrers" % id)

    def get_all_project_badges(self, id, host, token):
        """
        Gets a list of a project badges and its group badges

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_badges.html#project-badges-api

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/badges
        """
        return api.list_all(host, token, "projects/%d/badges" % id)

    def get_all_project_issues(self, id, host, token):
        """
        Get a list of issues for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/issues.html#list-project-issues

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues
        """
        return api.list_all(host, token, "projects/%d/issues" % id)

    def get_all_project_issue_notes(self, pid, iid, host, token):
        """
        Gets a list of all notes for a given issue

        GitLab API Doc: https://docs.gitlab.com/ee/api/notes.html#list-project-issue-notes

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/issues/:issue_iid/notes
        """
        return api.list_all(host, token, "projects/{0}/issues/{1}/notes".format(pid, iid))

    def get_all_project_boards(self, id, host, token):
        """
        Lists Issue Boards in the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/boards.html#project-board

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/boards
        """
        return api.list_all(host, token, "projects/%d/boards" % id)

    def get_all_project_labels(self, id, host, token):
        """
        Get all labels for a given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/labels.html#list-labels

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/labels
        """
        return api.list_all(host, token, "projects/%d/labels" % id)

    def get_all_project_milestones(self, id, host, token):
        """
        Returns a list of project milestones

        GitLab API Doc: https://docs.gitlab.com/ee/api/milestones.html#list-project-milestones

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/milestones
        """
        return api.list_all(host, token, "projects/%d/milestones" % id)

    def get_all_project_releases(self, id, host, token):
        """
        Returns a paginated list releases for a given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/releases/#list-releases

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/releases
        """
        return api.list_all(host, token, "projects/%d/releases" % id)

    def get_all_project_events(self, id, host, token):
        """
        Get a list of visible events for a particular project

        GitLab API Doc: https://docs.gitlab.com/ee/api/events.html#list-a-projects-visible-events

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:project_id/events
        """
        return api.list_all(host, token, "projects/%d/events" % id)

    def get_all_project_variables(self, id, host, token):
        """
        Get list of variables for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_level_variables.html#list-project-variables

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/variables
        """
        return api.list_all(host, token, "projects/%d/variables" % id)


    def create_project_variable(self, id, host, token, data):
        """
        Creates a new project variable

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_level_variables.html#create-variable

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the various data required for creating a project variable. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:id/variables
        """
        return api.generate_post_request(host, token, "projects/%d/variables" % id, json.dumps(data))

    def get_all_project_protected_branches(self, id, host, token):
        """
        Gets a list of protected branches from a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_branches.html#list-protected-branches

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/protected_branches
        """
        return api.list_all(host, token, "projects/%d/protected_branches" % id)

    def get_all_project_protected_environments(self, id, host, token):
        """
        Gets a list of protected environments from a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_environments.html#list-protected-environments

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/protected_environments
        """
        return api.list_all(host, token, "projects/%d/protected_environments" % id)

    def get_all_project_protected_tags(self, id, host, token):
        """
        Gets a list of protected tags from a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/protected_tags.html#list-protected-tags

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/protected_tags
        """
        return api.list_all(host, token, "projects/%d/protected_tags" % id)

    def get_all_project_deploy_keys(self, id, host, token):
        """
        Get a list of deploy keys for the given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/deploy_keys.html#list-project-deploy-keys

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/deploy_keys
        """
        return api.list_all(host, token, "projects/%d/deploy_keys" % id)

    def get_all_project_jobs(self, id, host, token):
        """
        Get a list of jobs in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/jobs.html#list-project-jobs

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/jobs
        """
        return api.list_all(host, token, "projects/%d/jobs" % id)

    def get_all_project_pipelines(self, id, host, token):
        """
        Get a list of pipelines in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipelines.html#list-project-pipelines

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/pipelines
        """
        return api.list_all(host, token, "projects/%d/pipelines" % id)

    def get_all_project_triggers(self, id, host, token):
        """
        Get a list of build triggers for a given project

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipeline_triggers.html#list-project-triggers

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/triggers
        """
        return api.list_all(host, token, "projects/%d/triggers" % id)

    def get_all_project_pipeline_variables(self, prid, piid, host, token):
        """
        Get variables of a given pipeline

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipelines.html#get-variables-of-a-pipeline

            :param: prid: (int) GitLab project ID
            :param: piid: (int) Pipeline ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/pipelines/:pipeline_id/variables
        """
        return api.list_all(host, token, "projects/{0}/pipelines/{1}/variables".format(prid, piid))

    def get_all_project_pipeline_schedules(self, id, host, token):
        """
        Get a list of the pipeline schedules of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/pipeline_schedules.html#get-all-pipeline-schedules

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/pipeline_schedules
        """
        return api.list_all(host, token, "projects/%d/pipeline_schedules" % id)

    def get_all_project_hooks(self, id, host, token):
        """
        Get a list of project hooks

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-project-hooks

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/hooks
        """
        return api.list_all(host, token, "projects/%d/hooks" % id)

    def get_all_project_push_rules(self, id, host, token):
        """
        Get the push rules of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#get-project-push-rules

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/push_rule
        """
        return api.list_all(host, token, "projects/%d/push_rule" % id)

    def get_all_project_approval_configuration(self, id, host, token):
        """
        Get the approval configuration of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_request_approvals.html#get-configuration

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/approvals
        """
        return api.list_all(host, token, "projects/%d/approvals" % id)

    def get_all_project_approval_rules(self, id, host, token):
        """
        Get the approval rules of a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/merge_request_approvals.html#get-project-level-rules

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/approval_rules
        """
        return api.list_all(host, token, "projects/%d/approval_rules" % id)

    def get_all_project_registry_repositories(self, id, host, token):
        """
        Get a list of registry repositories in a project

        GitLab API Doc: https://docs.gitlab.com/ee/api/container_registry.html#list-registry-repositories

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/registry/repositories
        """
        return api.list_all(host, token, "projects/%d/registry/repositories" % id)

    def get_all_project_registry_repositories_tags(self, pid, rid, host, token):
        """
        Get a list of tags for given registry repository

        GitLab API Doc: https://docs.gitlab.com/ee/api/container_registry.html#list-registry-repository-tags

            :param: pid: (int) GitLab project ID
            :param: rid: (int) Repository ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/registry/repositories/:repository_id/tags
        """
        return api.list_all(host, token, "projects/{0}/registry/repositories/{1}/tags".format(pid, rid))

    def get_all_project_feature_flags(self, id, host, token):
        """
        Gets all feature flags of the requested project

        GitLab API Doc: https://docs.gitlab.com/ee/api/feature_flags.html#list-feature-flags-for-a-project

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/feature_flags
        """
        return api.list_all(host, token, "projects/%d/feature_flags" % id)

    def get_all_project_custom_attributes(self, id, host, token):
        """
        Get all custom attributes on a resource

        GitLab API Doc: https://docs.gitlab.com/ee/api/custom_attributes.html#list-custom-attributes

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/custom_attributes
        """
        return api.list_all(host, token, "projects/%d/custom_attributes" % id)

    def get_all_project_snippets(self, host, token, project_id):
        """
        Get a list of project snippets

        GitLab API Doc: https://docs.gitlab.com/ee/api/notes.html#list-project-issue-notes

            :param: project_id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/snippets
        """
        return api.list_all(host, token, "projects/%d/snippets" % project_id)

    def get_single_project_snippets(self, host, token, project_id, snippet_id):
        """
        Get a single project snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/project_snippets.html#single-snippet

            :param: project_id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Response object containing the response to GET /projects/:id/snippets/:snippet_id
        """
        return api.generate_get_request(host, token, "projects/%d/snippets/%d" % (project_id, snippet_id))

    def get_project_snippet_awards(self, host, token, project_id, snipped_id):
        """
        Get a list of all award emoji for a specified project snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#list-an-awardables-award-emoji

            :param: project_id: (int) GitLab group ID
            :param: snipped_id: (int) Snipped ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/snippets/:snipped_id/award_emoji
        """
        return api.generate_get_request(host, token, "projects/%d/snippets/%d/award_emoji" % (project_id, snipped_id))

    def create_project_snippet_award(self, host, token, project_id, snipped_id, name):
        """
        Create an award emoji on the specified project snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#award-a-new-emoji

            :param: project_id: (int) GitLab project ID
            :param: snipped_id: (int) Snipped ID
            :param: name: (int) Name of the award
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/snippets/:snipped_id/award_emoji
        """
        return api.generate_post_request(host, token, "projects/%d/snippets/%d/award_emoji?name=%s" % (project_id, snipped_id, name), None)

    def get_project_snippet_note_awards(self, host, token, project_id, snipped_id, note_id):
        """
        Get all award emoji for an snippet note

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#get-an-award-emoji-for-a-comment

            :param: project_id: (int) GitLab group ID
            :param: snipped_id: (int) Snipped ID
            :param: note_id: (int) Note ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/snippets/:snipped_id/notes/:note_id/award_emoji
        """
        return api.generate_get_request(host, token, "projects/%d/snippets/%d/notes/%d/award_emoji" % (project_id, snipped_id, note_id))

    def create_project_snippet_note_award(self, host, token, project_id, snipped_id, note_id, name):
        """
        Create an award emoji on the specified project snippet note

        GitLab API Doc: https://docs.gitlab.com/ee/api/award_emoji.html#award-a-new-emoji-on-a-comment

            :param: project_id: (int) GitLab project ID
            :param: snipped_id: (int) Snipped ID
            :param: note_id: (int) Note ID
            :param: name: (int) Name of the award
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to POST /projects/:id/snippets/:snipped_id/notes/:note_id/award_emoji
        """
        return api.generate_post_request(host, token, "projects/%d/snippets/%d/notes/%d/award_emoji?name=%s" % (project_id, snipped_id, note_id, name), None)

    def get_project_snippet_notes(self, host, token, project_id, snipped_id):
        """
        Gets a list of all notes for a single snippet

        GitLab API Doc: https://docs.gitlab.com/ee/api/notes.html#list-all-snippet-notes

            :param: project_id: (int) GitLab group ID
            :param: snipped_id: (int) Snipped ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /projects/:id/snippets/:snippet_id/notes
        """
        return api.generate_get_request(host, token, "projects/%d/snippets/%d/notes" % (project_id, snipped_id))

    def get_environment(self, project_id, env_id, host, token):
        """
        Get a specific environment
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html#get-a-specific-environment

            :param: project_id: (int) GitLab project ID
            :param: env_id: (int) GitLab project environment ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /projects/:id/environments/:environment_id

        """
        return api.generate_get_request(host, token, "projects/{0}/environments/{1}".format(project_id, env_id))

    def get_all_environments(self, project_id, host, token):
        """
        Get a specific environment
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html#get-a-specific-environment

            :param: project_id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: RGenerator returning JSON of each result from GET /projects/:id/environments

        """
        return api.list_all(host, token, "projects/{}/environments".format(project_id))

    def create_environment(self, host, token, project_id, data):
        """
        Creates a new environment
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/environments.html#create-a-new-environment

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: project_id: (str) GitLab project ID
            :param: data: (dict) Object containing the necessary data for creating an environment. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:id/environments

        """
        return api.generate_post_request(host, token, "projects/{}/environments".format(project_id), json.dumps(data))

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
        return api.generate_delete_request(host, token, "projects/{0}/environments/{1}".format(project_id, env_id))