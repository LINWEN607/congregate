from helpers.base_class import base_class
from helpers import api
from helpers.misc_utils import strip_numbers, remove_dupes
from requests.exceptions import RequestException
from os import path
import json

class gl_branches_client(base_class):
    def get_branches(self, id, host, token):
        yield api.list_all(host, token, "projects/%d/repository/branches" % id)

    def get_protected_branches(self, id, host, token):
        yield api.list_all(host, token, "projects/%d/protected_branches" % id)

    def protect_branch(self, id, host, token, branch_name, push_access_level=None, merge_access_level=None, allowed_to_push=None, allowed_to_merge=None, allowed_to_unprotect=None):
        data = {
            "name": branch_name
        }
        if push_access_level is not None:
            data["push_access_level"] = push_access_level
        if merge_access_level is not None:
            data["merge_access_level"] = merge_access_level
        if allowed_to_push is not None:
            data["allowed_to_push"] = allowed_to_push
        if allowed_to_merge is not None:
            data["allowed_to_merge"] = allowed_to_merge
        if allowed_to_unprotect is not None:
            data["allowed_to_unprotect"] = allowed_to_unprotect
        return api.generate_post_request(host, token, "projects/%d/protected_branches" % id, data)

    