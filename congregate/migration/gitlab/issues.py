from helpers.base_class import BaseClass
from helpers import api
from helpers.misc_utils import strip_numbers, remove_dupes
from migration.gitlab.groups import GroupsClient
from requests.exceptions import RequestException
from os import path
import json


class IssuesClient(BaseClass):
    def get_all_project_issues(self, host, token, project_id):
        return api.list_all(host, token, "projects/%d/issues" % project_id)

    def get_all_group_issues(self, host, token, group_id):
        return api.list_all(host, token, "groups/%d/issues" % group_id)
