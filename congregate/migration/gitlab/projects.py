from congregate.helpers.base_class import base_class
from congregate.helpers import api

class gl_projects_client(base_class):
    def archive_project(self, host, token, id):
        return api.generate_post_request(host, token, "projects/%d/archive" % id, {}).json()

    def unarchive_project(self, host, token, id):
        return api.generate_post_request(host, token, "projects/%d/unarchive" % id, {}).json()