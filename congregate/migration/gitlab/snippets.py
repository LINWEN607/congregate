from helpers.base_class import BaseClass
from helpers import api
from helpers.misc_utils import strip_numbers, remove_dupes
from migration.gitlab.groups import GroupsClient
from requests.exceptions import RequestException
from os import path
import json


class SnippetsClient(BaseClass):
    def get_all_project_snippets(self, host, token, project_id):
        return api.list_all(host, token, "projects/%d/snippets" % project_id)

    def get_all_group_snippets(self, host, token, group_id):
        return api.list_all(host, token, "groups/%d/snippets" % group_id)

    def get_single_project_snippet(self, host, token, project_id, snippet_id):
        return api.generate_get_request(host, token, "projects/%d/snippets/%d" % (project_id, snippet_id))
