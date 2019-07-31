from congregate.helpers import api
import json

class UsersApi():

    def get_user(self, id, host, token):
        return api.generate_get_request(host, token, "users/%d" % id)

    def get_current_user(self, host, token):
        return api.generate_get_request(host, token, "user")

    def create_user(self, host, token, data):
        return api.generate_post_request(host, token, "users", json.dumps(data))

    def search_for_user_by_email(self, host, token, email):
        return api.list_all(host, token, "users?search=%s" % email, per_page=50)

    def create_user_impersonation_token(self, host, token, id, data):
        return api.generate_post_request(host, token, "users/%d/impersonation_tokens" % id, json.dumps(data))

    def delete_user_impersonation_token(self, host, token, user_id, token_id):
        return api.generate_delete_request(host, token, "users/%d/impersonation_tokens/%d" % (user_id, token_id))