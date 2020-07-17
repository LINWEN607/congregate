import json
import re

from urllib.error import HTTPError

from congregate.helpers import api, conf
from congregate.helpers import logger as log
from congregate.helpers.misc_utils import parse_query_params
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi


class gitlab_repo:
    def __init__(self):
        self.conf = conf.Config()
        self.project_repository_api = ProjectRepositoryApi()
        self.projects_api = ProjectsApi()
        self.l = log.myLogger(__name__)

    '''
        List repository branches
        https://docs.gitlab.com/ee/api/branches.html#list-repository-branches
    '''

    def get_branches(self, id, search=None, include_count=False):
        search_query = ""
        if search is not None:
            search_query = "?search=%s" % search
        try:
            resp = self.project_repository_api.get_all_project_repository_branches(
                self.conf.destination_host,
                self.conf.destination_token,
                id,
                search_query)
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
            resp = self.project_repository_api.get_single_project_repository_branch(
                self.conf.destination_host,
                self.conf.destination_token,
                id,
                branch)
            return json.load(resp)
        except HTTPError:
            return None

    '''
        List repository commits
        https://docs.gitlab.com/ee/api/commits.html#list-repository-commits
    '''

    def get_commits(self, pid, ref_name=None, since=None, until=None,
                    path=None, all=False, with_stats=False, include_count=False):
        params = locals()
        params.pop('self', None)
        params.pop('id', None)
        query_params = parse_query_params(params)
        resp = self.project_repository_api.get_all_project_repository_commits(
            pid,
            self.conf.destination_host,
            self.conf.destination_token,
            query_params)
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
            resp = self.project_repository_api.get_single_project_repository_commit(
                self.conf.destination_host,
                self.conf.destination_token,
                id,
                sha)
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
            resp = self.project_repository_api.get_project_repository_commit_refs(
                self.conf.destination_host,
                self.conf.destination_token,
                id,
                sha,
                query_param)
            return json.load(resp)
        except HTTPError:
            return None

    def get_mirror_url(self, id):
        resp = json.load(
            self.projects_api.get_project(
                id,
                self.conf.destination_host,
                self.conf.destination_token))
        return resp["import_url"]

    def search_for_project(self, name, group, search_name):
        for project in self.projects_api.search_for_project(self.conf.destination_host,
                                                            self.conf.destination_token,
                                                            name):
            # with_group = ("%s/%s" % (group.replace(" ", "_"), name.replace(" ", "-"))).lower()
            with_group = ("%s/%s" % (group.replace(" ", "_"),
                                     re.sub(r"\.| ", "-", name))).lower()
            pwn = project["path_with_namespace"]
            if project.get("path_with_namespace",
                           None) == search_name or pwn.lower() == with_group:
                self.l.info("Found project %s" % with_group)
                return project["id"]

        return None
