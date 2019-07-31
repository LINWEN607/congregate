from congregate.helpers import api
import json

class GroupsApi():
    def get_group(self, id, host, token):
        return api.generate_get_request(host, token, "groups/%d" % id)

    def search_for_group(self, name, host, token):
        return api.list_all(host, token, "groups?search=%s" % name)

    def create_group(self, host, token, data):
        return api.generate_post_request(host, token, "groups", json.dumps(data))

    def add_member_to_group(self, id, host, token, member):
        return api.generate_post_request(host, token, "groups/%d/members" % id, json.dumps(member))

    def get_all_groups(self, host, token):
        return api.list_all(host, token, "groups")

    def get_all_group_members(self, id, host, token):
        return api.list_all(host, token, "groups/%d/members" % id)

    def get_all_subgroups(self, id, host, token):
        return api.list_all(host, token, "groups/%d/subgroups" % id)

    def delete_group(self, id, host, token):
        return api.generate_delete_request(host, token, "groups/%d" % id)