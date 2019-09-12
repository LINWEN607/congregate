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

    def create_user(self, host, token, data):
        """
        Creates a new user
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#user-creation

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (dict) Object containing the necessary data for creating a user. Refer to the link above for specific examples
            :return: Response object containing the response to POST /users

        """
        return api.generate_post_request(host, token, "users", json.dumps(data))

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

    def create_user_impersonation_token(self, host, token, id, data):
        """
        It creates a new impersonation token. Note that only administrators can do this.
        
        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#create-an-impersonation-token

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: id: (int) GitLab user ID
            :param: data: (dict) Object containing the necessary data for creating a user. Refer to the link above for specific examples
            :return: Response object containing the response to POST /users/:id/impersonation_tokens

        """
        return api.generate_post_request(host, token, "users/%d/impersonation_tokens" % id, json.dumps(data))

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

    def block_user(self, host, token, user_id):
        """
        Blocks the specified user. Available only for admin.

        GitLab API Doc: https://docs.gitlab.com/ee/api/users.html#block-user

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: user_id: (int) GitLab user ID
            :return: 201 OK / 404 User Not Found / 403 Forbidden
        """
        return api.generate_post_request(host, token, "users/%d/block" % user_id, data=None)
