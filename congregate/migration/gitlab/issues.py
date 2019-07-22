from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.helpers.misc_utils import strip_numbers, remove_dupes
from congregate.migration.gitlab.groups import GroupsClient


class IssuesClient(BaseClass):
    def get_all_project_issues(self, host, token, project_id):
        return api.list_all(host, token, "projects/%d/issues" % project_id)

    def get_all_group_issues(self, host, token, group_id):
        return api.list_all(host, token, "groups/%d/issues" % group_id)

    def get_single_project_issues(self, host, token, project_id, issue_id):
        return api.generate_get_request(host, token, "projects/%d/issues/%d" % (project_id, issue_id))