from congregate.helpers import api, conf
from congregate.helpers import logger as log
from congregate.helpers.misc_utils import parse_query_params
from urllib2 import HTTPError
import urllib
import json
import re


class gitlab_repo:
    def __init__(self):
        self.conf = conf.ig()
        self.l = log.myLogger(__name__)

    '''
        List repository branches
        https://docs.gitlab.com/ee/api/branches.html#list-repository-branches
    '''

    def get_branches(self, id, search=None, include_count=False):
        if search is not None:
            search_query = "?search=%s" % search
        else:
            search_query = ""
        try:
            resp = api.generate_get_request(
                self.conf.destination_host,
                self.conf.destination_token,
                "projects/%d/repository/branches%s" %
                (id,
                 search_query))
            resp_json = json.load(resp)
            if include_count:
                resp_json = {
                    "response": resp_json,
                    "total-branches": resp.info().getheader('X-Total')
                }
            return resp_json
        except HTTPError:
            return None

    '''
        Get single repository branch
        https://docs.gitlab.com/ee/api/branches.html#get-single-repository-branch
    '''

    def get_single_branch(self, id, branch):
        try:
            resp = api.generate_get_request(
                self.conf.destination_host,
                self.conf.destination_token,
                "projects/%d/repository/branches/%s" %
                (id,
                 urllib.quote_plus(branch)))
            return json.load(resp)
        except HTTPError:
            return None

    '''
        List repository commits
        https://docs.gitlab.com/ee/api/commits.html#list-repository-commits
    '''

    def get_commits(self, id, ref_name=None, since=None, until=None,
                    path=None, all=False, with_stats=False, include_count=False):
        params = locals()
        params.pop('self', None)
        params.pop('id', None)
        query_params = parse_query_params(params)
        resp = api.generate_get_request(
            self.conf.destination_host,
            self.conf.destination_token,
            "projects/%d/repository/commits%s" %
            (id,
             query_params))
        if include_count:
            resp = {
                "response": resp,
                "total-commits": resp.info().getheader('X-Total')
            }
        return json.load(resp)

    '''
        Get a single commit.
        https://docs.gitlab.com/ee/api/commits.html#get-a-single-commit
    '''

    def get_single_commit(self, id, sha):
        try:
            resp = api.generate_get_request(
                self.conf.destination_host,
                self.conf.destination_token,
                "projects/%d/repository/commits/%s" %
                (id,
                 sha))
            return json.load(resp)
        except HTTPError:
            return None

    '''
        Get references a commit is pushed to.
        https://docs.gitlab.com/ee/api/commits.html#get-references-a-commit-is-pushed-to
    '''

    def get_refs_with_commits(self, id, sha, reftype=None):
        try:
            query_param = ""
            if reftype is not None:
                query_param = "?type=%s" % reftype

            resp = api.generate_get_request(
                self.conf.destination_host,
                self.conf.destination_token,
                "projects/%d/repository/commits/%s/refs%s" %
                (id,
                 sha,
                 query_param))
            return json.load(resp)
        except HTTPError:
            return None

    def get_mirror_url(self, id):
        resp = json.load(
            api.generate_get_request(
                self.conf.destination_host,
                self.conf.destination_token,
                "projects/%d" %
                id))
        return resp["import_url"]

    def search_for_project(self, name, group, search_name):
        for project in api.list_all(self.conf.destination_host,
                                    self.conf.destination_token,
                                    "projects",
                                    params={
                                        "search": urllib.quote_plus(name)
                                    }):
            # with_group = ("%s/%s" % (group.replace(" ", "_"), name.replace(" ", "-"))).lower()
            with_group = ("%s/%s" % (group.replace(" ", "_"), re.sub(r"\.| ", "-", name))).lower()
            pwn = project["path_with_namespace"]
            if project.get("path_with_namespace",
                           None) == search_name or pwn.lower() == with_group:
                self.l.info("Found project %s" % with_group)
                return project["id"]

        return None
