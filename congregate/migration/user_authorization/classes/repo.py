import sys
# print('sys path: ', sys.path)
from ..util import json_util
import re
import requests
from itertools import permutations
from ..util.misc import replace_multiple_pairs


class Repo(object):
    """
    Given a bitbucket https clone URL
    """

    def __init__(self, https_clone_url, repo_name, bitbucket_instance, gitlab_instance):
        self.bitbucket_instance = bitbucket_instance
        self.gitlab_instance = gitlab_instance
        self.https_clone_url = https_clone_url
        self.repo_name = repo_name
        self.repo_slug = self.get_repo_slug_from_clone_url(https_clone_url)
        self.project_key = self.get_project_key_from_clone_url(https_clone_url)
        self.bitbucket_api_repo_data = self.get_bitbucket_api_repo_data(repo_name=repo_name, repo_slug=self.repo_slug,
                                                                        project_key=self.project_key,
                                                                        bitbucket_instance=self.bitbucket_instance)
        self.bitbucket_project_name = self.bitbucket_api_repo_data['project']['name']
        self.gitlab_project_name = repo_name
        self.gitlab_group_name = self.bitbucket_project_name
        self.gitlab_api_repo_data = self.get_gitlab_api_repo_data(gitlab_instance=self.gitlab_instance,
                                                                  gitlab_project_name=self.gitlab_project_name,
                                                                  gitlab_group_name=self.gitlab_group_name)
        self.gitlab_project_id = self.get_gitlab_project_id(self.gitlab_api_repo_data)
        self.gitlab_group_id = self.get_gitlab_group_id(self.gitlab_api_repo_data)
        self.exists_in_gitlab = self.exists_in_gitlab()
        self.bitbucket_repo_users = self.get_bitbucket_repo_users()
        self.bitbucket_project_users = self.get_bitbucket_project_users()

    def get_bitbucket_repo_users(self):
        # From project key and repo slug, get repo users/permissions
        url_extension = '/projects/%s/repos/%s/permissions/users' % (self.project_key, self.repo_slug)
        resp = self.bitbucket_instance.api_request(url_extension=url_extension, request_type='get').json()
        return resp['values']

    def get_bitbucket_project_users(self):
        # From project key and repo slug, get repo users/permissions
        url_extension = '/projects/%s/permissions/users' % (self.project_key)
        resp = self.bitbucket_instance.api_request(url_extension=url_extension, request_type='get').json()
        return resp['values']

    def get_bitbucket_users_at_level(self, level):
        if level.value == 'bitbucket_repo':
            return self.get_bitbucket_repo_users()
        elif level.value == 'bitbucket_project':
            return self.get_bitbucket_project_users()

    def has_bitbucket_repo_user(self, user):
        if self.user_is_in_bitbucket_users_list(bitbucket_users_list=self.bitbucket_repo_users, user=user):
            return True
        else:
            return False

    def exists_in_gitlab(self):
        kwargs = {
            'gitlab_instance': self.gitlab_instance,
            'gitlab_project_name': self.gitlab_project_name,
            'gitlab_group_name': self.gitlab_group_name
        }
        data = self.get_gitlab_api_repo_data(**kwargs)
        exists_in_gitlab = False if data == None else True
        return exists_in_gitlab

    def get_gitlab_id_at_level(self, level):
        if level.value == 'bitbucket_repo':
            id = self.gitlab_project_id
        elif level.value == 'bitbucket_project':
            id = self.gitlab_group_id
        return id

    @staticmethod
    def get_gitlab_project_id(gitlab_api_repo_data):
        try:
            id = gitlab_api_repo_data['id']
        except Exception as e:
            id = None
        return id

    @staticmethod
    def get_gitlab_group_id(gitlab_api_repo_data):
        try:
            id = gitlab_api_repo_data['namespace']['id']
        except Exception as e:
            id = None
        return id

    @staticmethod
    def get_gitlab_users_at_level(gitlab_instance, gitlab_api_bridge, gitlab_id_at_level):
        """
        Gets a list of users at the specified level from the GitLab API.
        :param gitlab_api_bridge: Either projects or groups
        :param gitlab_id_at_level: The ID of the GitLab level entity. E.j. either the gitlab project id or group id
        :return: A list of users at the specified level
        """
        url_extension = '/%s/%d/members' % (gitlab_api_bridge, gitlab_id_at_level)
        response = gitlab_instance.api_request(url_extension=url_extension, request_type='get').json()
        return response

    @staticmethod
    def get_bitbucket_api_repo_data(repo_name, repo_slug, project_key, bitbucket_instance):
        url_extension = re.sub('\n', '', '/projects/%s/repos/%s' % (project_key, repo_slug))
        response = bitbucket_instance.api_request(url_extension=url_extension, request_type='get', params={"name": repo_name}).json()
        # response = requests.get(url, params={"name": repo_name}, auth=(username, password),
        #                       proxies=PROXY_LIST).json()
        if response['project']['key'].lower() == project_key.lower():
            return response
        raise RuntimeError("No repo match found")

    @staticmethod
    def get_gitlab_api_repo_data(gitlab_instance, gitlab_project_name, gitlab_group_name):
        url_extension = '/projects'
        params = {'search': gitlab_project_name}
        # response = requests.get(url, params={'search': gitlab_project_name}, headers=api_headers).json()
        response = gitlab_instance.api_request(url_extension=url_extension, request_type='get', params=params).json()
        for item in response:
            if Repo.bitbucket_and_gitlab_names_match(gitlab_group_name, item['namespace']['name']):
                return item
        return None

    @staticmethod
    def get_project_key_from_clone_url(https_clone_url):
        project_key = https_clone_url.split('/')[-2]
        return project_key

    @staticmethod
    def get_repo_slug_from_clone_url(https_url):
        assert '.git' in https_url, "The https clone url is invalid: %s" % https_url
        str = https_url.split('/')[-1]
        repo_slug = str.split('.git')[-2]
        return repo_slug

    @staticmethod
    def bitbucket_and_gitlab_names_match(bitbucket_name, gitlab_name):
        """
        Function that checks if a bitbucket repo or project name and a gitlab project or group name match for a
        repo (GitLab project). It does this by replacing the characters that might be modified during the congregate
        creation process.
        :param bitbucket_name:
        :param gitlab_name:
        :return: True or False if one of the name possibilities match
        """
        input_names = [bitbucket_name, gitlab_name]
        for name in input_names:
            assert name != None and len(name), "Invalid input: ".format(bitbucket_name)
        bitbucket_name_possibilities = Repo.get_name_possibilities(bitbucket_name)
        gitlab_name_possibilities = Repo.get_name_possibilities(gitlab_name)
        names_match = any([x == y for x in bitbucket_name_possibilities for y in gitlab_name_possibilities])
        return names_match

    @staticmethod
    def get_name_possibilities(name):
        """
        Function that gets the name possibilities of a bitbucket or gitlab entity name by replacing characters that
        might have been changed during the creation process in congregate
        :param repo_name:
        :return:
        """
        possible_replace_pairs = [
            (" ", "_"),
            (" ", "-")
        ]
        replace_pair_permutations = permutations(possible_replace_pairs)
        name_possibilities = [replace_multiple_pairs(str=name, replace_pairs=replace_pair) for replace_pair in replace_pair_permutations]
        return name_possibilities

