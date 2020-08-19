from congregate.migration.bitbucket.api import base as api

class GroupsApi():

    def get_all_groups(self, host):
        return api.list_all(host, "admin/groups")

    def get_all_group_users(self, host, group):
        return api.list_all(host, f"admin/groups/more-members?context={group}")