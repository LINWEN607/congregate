from congregate.helpers import api
from urllib import quote_plus
import json

class ProjectsApi():

    def search_for_project(self, host, token, name):
        return api.list_all(host, token, "projects?search=%s" % quote_plus(name))

    def get_project(self, id, host, token):
        return api.generate_get_request(host, token, "projects/%d" % id)

    def get_all_projects(self, host, token):
        return api.list_all(host, token, "projects")

    def get_members(self, id, host, token):
        return api.list_all(host, token, "projects/%d/members" % id)

    def add_member_to_group(self, id, host, token, member):
        return api.generate_post_request(host, token, "projects/%d/members" % id, json.dumps(member))

    def archive_project(self, host, token, id):
        return api.generate_post_request(host, token, "projects/%d/archive" % id, {}).json()

    def unarchive_project(self, host, token, id):
        return api.generate_post_request(host, token, "projects/%d/unarchive" % id, {}).json()
    
    def delete_project(self, host, token, id):
        return api.generate_delete_request(host, token, "projects/%d" % id)

    def add_shared_group(self, host, token, id, group):
        return api.generate_post_request(host, token, "projects/%d/share" % id, json.dumps(group))

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
