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

    def add_shared_group(self, host, token, id, group):
        """
        Allow to share project with group
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#share-project-with-group

            :param: id: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: group: (dict) Object containing the necessary data for the shared group
            :return: Response object containing the response to POST /projects/:id/share

        """
        return api.generate_post_request(host, token, "projects/%d/share" % id, json.dumps(group))

    def get_all_project_badges(self, host, token, id):
        """
        List all badges of a project

        GitLab API doc: https://docs.gitlab.com/ee/api/project_badges.html#list-all-badges-of-a-project

            :param: id: (int) GitLab project ID
            :yield: Generator containing JSON from GET /projects/:id/badges
        """
        return api.list_all(host, token, "projects/%d/badges" % id)

    def edit_project_badge(self, host, token, id, badge_id, data=None):
        """
        Edit a badge of a project

        GitLab API doc: https://docs.gitlab.com/ee/api/project_badges.html#edit-a-badge-of-a-project

            :param: id: (int) GitLab project ID
            :param: badge_id: (int) The badge ID
            :param: link_url: (str) URL of the badge link
            :param: image_url: (str) URL of the badge image
            :return: Response object containing the response to PUT /projects/:id/badges/:badge_id
        """
        return api.generate_put_request(host, token, "projects/%d/badges/%d" % (id, badge_id), json.dumps(data))

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
            data = {
                "name": name
            }
        
        if headers is not None:
            return api.generate_post_request(host, token, "projects", json.dumps(data), headers=headers)
        else:
            return api.generate_post_request(host, token, "projects", json.dumps(data))
