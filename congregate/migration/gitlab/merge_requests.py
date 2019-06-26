from helpers.base_class import BaseClass
from helpers import api
from helpers.misc_utils import strip_numbers, remove_dupes
from migration.gitlab.groups import GroupsClient
from requests.exceptions import RequestException
from os import path
import json

class MergeRequestsClient(BaseClass):
    def get_all_project_merge_requests(self, host, token, project_id):
        return api.list_all(host, token, "projects/%d/merge_requests" % project_id)

    def get_all_group_merge_requests(self, host, token, group_id):
        return api.list_all(host, token, "groups/%d/merge_requests" % group_id)

    def get_single_project_merge_request(self, host, token, project_id, mr_id):
        return api.generate_get_request(host, token, "projects/%d/merge_requests/%d" % (project_id, mr_id))
