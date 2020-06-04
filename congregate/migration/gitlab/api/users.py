import json
from congregate.helpers import api


class UsersApi():

    def get_user(self, id, host, token):
        """
        Get a single user

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#single-user

            :param: id: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:id
        """
        return api.generate_get_request(host, token, "users/%d" % id)

    def get_user_email(self, id, host, token):
        return self.get_user(id, host, token).json()["email"]

    def get_current_user(self, host, token):
        """
        Get the current user based on access token

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#list-current-user-for-admins

            :param: id: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /user
        """
        return api.generate_get_request(host, token, "user").json()

    def get_all_users(self, host, token):
        """
        Get a list of users.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#for-admins

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /users
        """
        return api.list_all(host, token, "users")

    def create_user(self, host, token, data, message=None):
        """
        Creates a new user

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#user-creation

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the necessary data for creating a user. Refer to the link above for specific examples
            :return: Response object containing the response to POST /users
        """
        if not message:
            message = "Creating new user %s with payload %s" % (
                data["email"], str(data))
        return api.generate_post_request(host, token, "users", json.dumps(data), description=message)

    def delete_user(self, host, token, id, hard_delete=False):
        """
        Delete a single user

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#user-deletion

            :param: id: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: hard_delete: (boo) Option to delete user contributions and solely owned groups
            :return: Response object containing a 204 (No Content) or 404 (Group not found) from DELETE /users/:id
        """
        return api.generate_delete_request(host, token, "users/{0}?hard_delete={1}".format(id, hard_delete))

    def search_for_user_by_email(self, host, token, email):
        """
        Searches for a user by email

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#for-admins

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: email: (str) Email of the specific user being searched
            :yield: Generator containing JSON results from GET /users?search=:email
        """
        return api.list_all(host, token, "users?search=%s" % email, per_page=50)

    def search_for_user_by_username(self, host, token, username):
        """
        Searches for a user by username

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#for-admins

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: email: (str) Email of the specific user being searched
            :yield: Generator containing JSON results from GET /users?search=:email
        """
        return api.list_all(host, token, "users?username=%s" % username, per_page=50)

    def create_user_impersonation_token(self, host, token, id, data, message=None):
        """
        It creates a new impersonation token. Note that only administrators can do this.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#create-an-impersonation-token

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: id: (int) GitLab user ID
            :param: data: (dict) Object containing the necessary data for creating a user. Refer to the link above for specific examples
            :return: Response object containing the response to POST /users/:id/impersonation_tokens
        """
        if not message:
            message = "Creating impersonation token for %d" % id
        return api.generate_post_request(host, token, "users/%d/impersonation_tokens" % id, json.dumps(data), description=message)

    def delete_user_impersonation_token(self, host, token, user_id, token_id):
        """
        Revokes an impersonation token. Note that only administrators can do this.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#revoke-an-impersonation-token

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: user_id: (int) GitLab user ID
            :param: token: (int) GitLab user impersonation token ID
            :return: Response object containing a 202 (accepted) or 404 (Group not found) from DELETE /users/:user_id/impersonation_tokens/:impersonation_token_id
        """
        return api.generate_delete_request(host, token, "users/%d/impersonation_tokens/%d" % (user_id, token_id))

    def block_user(self, host, token, user_id, message=None):
        """
        Blocks the specified user. Available only for admin.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#block-user

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: user_id: (int) GitLab user ID
            :return: 201 OK / 404 User Not Found / 403 Forbidden
        """
        if not message:
            message = "Blocking user %d" % user_id
        return api.generate_post_request(host, token, "users/%d/block" % user_id, data=None)

    def get_all_user_contribution_events(self, id, host, token):
        """
        Get the contribution events for the specified user

        GitLab API Doc: https://docs.gitlab.com/ee/api/events.html#get-user-contribution-events

            :param: id: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Generator returning JSON of each result from GET /users/:id/events
        """
        return api.generate_get_request(host, token, "users/%d/events" % id)

    def get_all_user_memberships(self, id, host, token):
        """
        Lists all projects and groups a user is a member of

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#user-memberships-admin-only

            :param: id: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Generator returning JSON of each result from GET /users/:id/memberships
        """
        return api.generate_get_request(host, token, "users/%d/memberships" % id)

    def get_user_status(self, id, host, token):
        """
        Get the status of a user

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#get-the-status-of-a-user

            :param: id: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:id_or_username/status
        """
        return api.generate_get_request(host, token, "users/%d/status" % id)

    def get_all_user_ssh_keys(self, uid, host, token):
        """
        Get a list of a specified user SSH keys.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#list-ssh-keys-for-user

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:id_or_username/keys
        """
        return api.generate_get_request(host, token, "users/{}/keys".format(uid))

    def create_user_ssh_key(self, host, token, uid, data, message=None):
        """
        Create new key owned by specified user. Available only for admin

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#add-ssh-key-for-user

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: uid: (int) GitLab user ID
            :param: data: (dict) Object containing the necessary data for creating an SSH key. Refer to the link above for specific examples
            :return: Response object containing the response to POST /users/:id/keys
        """
        if not message:
            message = "Creating SSH key for {}".format(uid)
        return api.generate_post_request(host, token, "users/{}/keys".format(uid), json.dumps(data), description=message)

    def get_all_user_gpg_keys(self, uid, host, token):
        """
        Get a list of a specified user GPG keys. Available only for admins.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#list-all-gpg-keys-for-given-user

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:id/gpg_keys
        """
        return api.generate_get_request(host, token, "users/{}/gpg_keys".format(uid))

    def create_user_gpg_key(self, host, token, uid, data, message=None):
        """
        Create new GPG key owned by the specified user. Available only for admins.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#add-a-gpg-key-for-a-given-user

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: uid: (int) GitLab user ID
            :param: data: (dict) Object containing the necessary data for creating a GPG key. Refer to the link above for specific examples
            :return: Response object containing the response to POST /users/:id/gpg_keys
        """
        if not message:
            message = "Creating GPG key for {}".format(uid)
        return api.generate_post_request(host, token, "users/{}/gpg_keys".format(uid), json.dumps(data), description=message)

    def get_all_user_projects(self, id, host, token):
        """
        Get a list of visible projects owned by the given user

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-user-projects

            :param: id: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:user_id/projects
        """
        return api.generate_get_request(host, token, "users/%d/projects" % id)

    def get_all_user_emails(self, id, host, token):
        """
        Get a list of emails for a give user

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#list-emails-for-user

            :param: id: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:id/emails
        """
        return api.generate_get_request(host, token, "users/%d/emails" % id)

    def get_all_user_custom_attributes(self, id, host, token):
        """
        Get all custom attributes on a user

        https://docs.gitlab.com/ee/api/custom_attributes.html#list-custom-attributes

            :param: id: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /users/:id/custom_attributes
        """
        return api.list_all(host, token, "users/%d/custom_attributes" % id)

    def get_user_counts(self, host, token):
        """
        Get the counts (same as in top right menu) of the currently signed in user

        https://docs.gitlab.com/ee/api/users.html#user-counts

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield:  Response object containing the response to GET /user_counts
        """
        return api.generate_get_request(host, token, "user_counts")
