from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.helpers.misc_utils import strip_numbers, remove_dupes

class MergeRequestsApi(BaseClass):
    def get_all_project_merge_requests(self, host, token, project_id):
        return api.list_all(host, token, "projects/%d/merge_requests" % project_id)

    def get_all_group_merge_requests(self, host, token, group_id):
        return api.list_all(host, token, "groups/%d/merge_requests" % group_id)

    def get_single_project_merge_requests(self, host, token, project_id, mr_id):
        return api.generate_get_request(host, token, "projects/%d/merge_requests/%d" % (project_id, mr_id))
