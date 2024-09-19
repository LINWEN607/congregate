import json
from urllib.parse import quote_plus
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper


class UsersApi(GitLabApiWrapper):

    def get_user(self, uid, host, token):
        """
        Get a single user

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#single-user

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:uid
        """
        return self.api.generate_get_request(host, token, f"users/{uid}")

    def get_user_email(self, uid, host, token):
        returned = self.get_user(uid, host, token).json()
        return returned.get("email", returned.get("public_email", ""))

    def get_current_user(self, host, token, headers=None):
        """
        Get the current user based on access token

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#list-current-user-for-admins

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /user
        """
        return self.api.generate_get_request(host, token, "user", headers=headers)

    def modify_user(self, uid, host, token, data=None):
        """
        Modifies an existing user. Only administrators can change attributes of a user.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#user-modification

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to PUT /users/:uid
        """
        return self.api.generate_put_request(host, token, f"users/{uid}", data=json.dumps(data))

    def get_all_users(self, host, token):
        """
        Get a list of all instance users, excluding internal and bot.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#for-admins

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /users
        """
        return self.api.list_all(host, token, "users?exclude_internal=true&without_project_bots=true")

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
            message = f"Creating new user {data['email']} with payload {str(data)}"
        return self.api.generate_post_request(host, token, "users", json.dumps(data), description=message)

    def delete_user(self, host, token, uid, hard_delete=False):
        """
        Delete a single user

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#user-deletion

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: hard_delete: (boo) Option to delete user contributions and solely owned groups
            :return: Response object containing a 204 (No Content) or 404 (Group not found) from DELETE /users/:uid
        """
        return self.api.generate_delete_request(host, token, f"users/{uid}?hard_delete={hard_delete}")

    def search_for_user_by_email(self, host, token, email):
        """
        Searches for a user by email

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#for-administrators

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: email: (str) Email of the specific user being searched
            :yield: Generator containing JSON results from GET /users?search=:email
        """
        return self.api.list_all(host, token, f"users?search={quote_plus(email)}", per_page=10)

    def search_for_user_by_username(self, host, token, username):
        """
        Searches for a user by username

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#for-non-administrator-users

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: username: (str) Username of the specific user being searched
            :yield: Generator containing JSON results from GET /users?username=:username
        """
        return self.api.list_all(host, token, f"users?username={username}", per_page=10)

    def create_user_impersonation_token(self, host, token, uid, data, message=None):
        """
        It creates a new impersonation token. Note that only administrators can do this.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#create-an-impersonation-token

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: uid: (int) GitLab user ID
            :param: data: (dict) Object containing the necessary data for creating a user. Refer to the link above for specific examples
            :return: Response object containing the response to POST /users/:uid/impersonation_tokens
        """
        if not message:
            message = f"Creating impersonation token for {uid}"
        return self.api.generate_post_request(host, token, f"users/{uid}/impersonation_tokens", json.dumps(data), description=message)

    def delete_user_impersonation_token(self, host, token, uid, token_id):
        """
        Revokes an impersonation token. Note that only administrators can do this.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#revoke-an-impersonation-token

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: uid: (int) GitLab user ID
            :param: token_id: (int) GitLab user impersonation token ID
            :return: Response object containing a 202 (accepted) or 404 (Group not found) from DELETE /users/:user_id/impersonation_tokens/:impersonation_token_id
        """
        return self.api.generate_delete_request(host, token, f"users/{uid}/impersonation_tokens/{token_id}")

    def block_user(self, host, token, uid, message=None):
        """
        Blocks the specified user. Available only for admin.

        GitLab API Doc: https://docs.gitlab.com/ee/api/user_moderation.html#block-a-user

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: uid: (int) GitLab user ID
            :return: 201 OK / 404 User Not Found / 403 Forbidden
        """
        if not message:
            message = f"Blocking user {uid}"
        return self.api.generate_post_request(host, token, f"users/{uid}/block", data=None)

    def unblock_user(self, host, token, uid, message=None):
        """
        Unblocks the specified user. Available only for admin.

        GitLab API Doc: https://docs.gitlab.com/ee/api/user_moderation.html#unblock-a-user

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: uid: (int) GitLab user ID
            :return: 201 OK / 404 User Not Found / 403 Forbidden
        """
        if not message:
            message = f"Unblocking user {uid}"
        return self.api.generate_post_request(host, token, f"users/{uid}/unblock", data=None)

    def get_all_user_contribution_events(self, uid, host, token):
        """
        Get the contribution events for the specified user

        GitLab API Doc: https://docs.gitlab.com/ee/api/events.html#get-user-contribution-events

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Generator returning JSON of each result from GET /users/:uid/events
        """
        return self.api.generate_get_request(host, token, f"users/{uid}/events")

    def get_all_user_memberships(self, uid, host, token):
        """
        Lists all projects and groups a user is a member of

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#user-memberships-admin-only

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Generator returning JSON of each result from GET /users/:uid/memberships
        """
        return self.api.generate_get_request(host, token, f"users/{uid}/memberships")

    def get_user_status(self, uid, host, token):
        """
        Get the status of a user

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#get-the-status-of-a-user

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:uid_or_username/status
        """
        return self.api.generate_get_request(host, token, f"users/{uid}/status")

    def get_all_user_ssh_keys(self, uid, host, token):
        """
        Get a list of a specified user SSH keys.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#list-ssh-keys-for-user

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:uid_or_username/keys
        """
        return self.api.list_all(host, token, f"users/{uid}/keys")

    def create_user_ssh_key(self, host, token, uid, data, message=None):
        """
        Create new key owned by specified user. Available only for admin

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#add-ssh-key-for-user

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: uid: (int) GitLab user ID
            :param: data: (dict) Object containing the necessary data for creating an SSH key. Refer to the link above for specific examples
            :return: Response object containing the response to POST /users/:uid/keys
        """
        if not message:
            message = f"Creating SSH key for {uid}"
        return self.api.generate_post_request(host, token, f"users/{uid}/keys", json.dumps(data), description=message)

    def get_all_user_gpg_keys(self, uid, host, token):
        """
        Get a list of a specified user GPG keys. Available only for admins.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#list-all-gpg-keys-for-given-user

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:uid/gpg_keys
        """
        return self.api.list_all(host, token, f"users/{uid}/gpg_keys")

    def create_user_gpg_key(self, host, token, uid, data, message=None):
        """
        Create new GPG key owned by the specified user. Available only for admins.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#add-a-gpg-key-for-a-given-user

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: uid: (int) GitLab user ID
            :param: data: (dict) Object containing the necessary data for creating a GPG key. Refer to the link above for specific examples
            :return: Response object containing the response to POST /users/:uid/gpg_keys
        """
        if not message:
            message = f"Creating GPG key for {uid}"
        return self.api.generate_post_request(host, token, f"users/{uid}/gpg_keys", json.dumps(data), description=message)

    def get_all_user_projects(self, uid, host, token):
        """
        Get a list of visible projects owned by the given user

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-user-projects

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:user_id/projects
        """
        return self.api.generate_get_request(host, token, f"users/{uid}/projects")

    def get_all_user_emails(self, uid, host, token):
        """
        Get a list of emails for a give user

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#list-emails-for-user

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :return: Response object containing the response to GET /users/:uid/emails
        """
        return self.api.generate_get_request(host, token, f"users/{uid}/emails")

    def get_all_user_custom_attributes(self, uid, host, token):
        """
        Get all custom attributes on a user

        https://docs.gitlab.com/ee/api/custom_attributes.html#list-custom-attributes

            :param: uid: (int) GitLab user ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /users/:uid/custom_attributes
        """
        return self.api.list_all(host, token, f"users/{uid}/custom_attributes")

    def get_user_counts(self, host, token):
        """
        Get the counts (same as in top right menu) of the currently signed in user

        https://docs.gitlab.com/ee/api/users.html#user-counts

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield:  Response object containing the response to GET /user_counts
        """
        return self.api.generate_get_request(host, token, "user_counts")

    def add_user_email(self, host, token, uid, data, message=None):
        """
        Create new email owned by specified user. Available only for administrator

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#add-email-for-user

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: uid: (str) ID of specified user
            :param: data: (dict) Object containing the necessary data for adding a user email. Refer to the link above for specific examples
            :return: Response object containing the response to POST /users/:id/emails
        """
        if not message:
            message = f"Adding new email '{data['email']}' to user {uid}"
        return self.api.generate_post_request(host, token, f"users/{uid}/emails", json.dumps(data), description=message)
