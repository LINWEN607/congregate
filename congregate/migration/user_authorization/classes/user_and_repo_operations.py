from ..classes.level import Level
import json
from ..util.misc import debug_print


class User_And_Repo_Operations(object):
    def __init__(self, repo, user):
        self.repo = repo
        self.user = user
        self.user_is_bitbucket_repo_user = self.user_is_in_bitbucket_users_list(
            bitbucket_users_list=repo.bitbucket_repo_users, user=self.user)
        self.user_is_bitbucket_project_user = self.user_is_in_bitbucket_users_list(
            bitbucket_users_list=repo.bitbucket_project_users, user=self.user)
        self.bitbucket_repo_level_user_permission = self.get_bitbucket_user_permission_at_level(level=Level('bitbucket_repo'))
        self.bitbucket_project_level_user_permission = self.get_bitbucket_user_permission_at_level(level=Level('bitbucket_project'))
        # self.gitlab_project_level_user_permission = self.get_gitlab_user_permission_at_level(level=Level('bitbucket_repo'))
        # self.gitlab_group_level_user_permission = self.get_gitlab_user_permission_at_level(level=Level('bitbucket_project'))
        self.bitbucket_to_gitlab_permission_map = {
            "PROJECT_ADMIN": 50,
            "PROJECT_WRITE": 30,
            "PROJECT_READ": 20,
            "REPO_ADMIN": 40,
            "REPO_WRITE": 30,
            "REPO_READ": 20
        }

    def get_bitbucket_user_permission_at_level(self, level):
        if self.user_is_bitbucket_user_at_level(level):
            users_list_at_level = self.repo.get_bitbucket_users_at_level(level)
            bitbucket_user_data = self.get_bitbucket_user_data_from_bitbucket_users_list(
                bitbucket_users_list=users_list_at_level,
                first_name=self.user.first_name,
                last_name=self.user.last_name
            )
            permission = self.get_permission_from_bitbucket_user_data(user_data=bitbucket_user_data)
            return permission
        else:
            return None

    def user_is_bitbucket_user_at_level(self, level):
        if level.value == 'bitbucket_repo':
            return self.user_is_bitbucket_repo_user
        elif level.value == 'bitbucket_project':
            return self.user_is_bitbucket_project_user



    def correct_user_permission_at_level(self, user_already_is_user_at_level, level):
        """
        Function that makes the GitLab permissions of the user at the specified level match those of Bitbucket. Only works for already existing users
        :param level: A level object representing the gitlab project level or gitlab group level
        :return: A boolean indicating whether the permissions were updated successfully. This is based on the status code returned from the request.
        """
        gitlab_entity_id = self.repo.get_gitlab_id_at_level(level)
        if user_already_is_user_at_level:
            request_type = 'put'
            url_extension = '/%s/%d/members/%d' % (level.gitlab_api_bridge, gitlab_entity_id, self.user.get_gitlab_id(self.repo.gitlab_instance))
        elif not user_already_is_user_at_level:
            request_type = 'post'
            url_extension = '/%s/%d/members' % (level.gitlab_api_bridge, gitlab_entity_id)
        bitbucket_permission = self.get_bitbucket_user_permission_at_level(level)
        user_id = self.user.get_gitlab_id(gitlab_instance=self.repo.gitlab_instance)
        corresponding_gitlab_permission = self.get_corresponding_gitlab_permission(bitbucket_permission)
        data = {
            "user_id": user_id,
            "access_level": corresponding_gitlab_permission
        }
        for k, v in data.items():
            assert v != None, "Invalid data component. {} cannot be {}".format(k, v)
        response = self.repo.gitlab_instance.api_request(request_type=request_type, url_extension=url_extension, data=data)
        status_code = response.status_code
        success_status_codes = [200, 201]
        if status_code in success_status_codes:
            return True
        else:
            return False

    def synchronize_gitlab_user_permission(self, permission_level):
        """
        Function that verifies the user's permission for the specified permission level is correct. If it's not correct,
        it corrects the GitLab permissions.
        :param permission_level: The level at which the permissions should be synchronized. Can be repo or project
        """
        # level_info = get_level_info(permission_level)

    def user_is_gitlab_user_at_level(self, level):
        get_gitlab_users_at_level_args = {
            'gitlab_instance': self.repo.gitlab_instance,
            'gitlab_api_bridge': level.gitlab_api_bridge,
            'gitlab_id_at_level': self.repo.get_gitlab_id_at_level(level)
        }
        users_list = self.repo.get_gitlab_users_at_level(**get_gitlab_users_at_level_args)
        # if level.get_gitlab_level_name() == 'GitLab project':
        #     debug_print('gitlab level', level.get_gitlab_level_name())
        #     debug_print('users_list', users_list)
        if self.user_is_in_gitlab_users_list(gitlab_users_list=users_list, user=self.user):
            return True
        return False

    def get_gitlab_user_permission_at_level(self, level):
        users_list = self.repo.get_gitlab_users_at_level(gitlab_instance=self.repo.gitlab_instance,
                                                         gitlab_api_bridge=level.gitlab_api_bridge,
                                                         gitlab_id_at_level=self.repo.get_gitlab_id_at_level(level))
        user_data = self.get_user_data_from_gitlab_users_list(users_list=users_list, user=self.user)
        try:
            permission = user_data['access_level']
        except Exception as e:
            permission = None
        return permission


    def add_gitlab_user_permissions_at_level(self, gitlab_entity_id, user_id, permission_num, level, gitlab_instance, request_type='post'):
        """
        A function that adds an already existing GitLab user to a GitLab project or group with the specified permissions.
        :param gitlab_entity_id:
        :param user_id:
        :param permission_num:
        :param level:
        :param gitlab_instance:
        :return:
        """
        data = {
            "user_id": user_id,
            "access_level": permission_num
        }
        # data = '&'.join(['%s=%s' % (key, val) for key, val in data_dict.items()])
        url_extension = '/%s/%d/members' % (level.gitlab_api_bridge, gitlab_entity_id)
        resp = gitlab_instance.api_request(request_type=request_type, url_extension=url_extension, data=data)
        return resp.status_code

    def bitbucket_and_gitlab_permissions_match(self, bitbucket_permission, gitlab_permission):
        if self.bitbucket_to_gitlab_permission_map.get(bitbucket_permission) == gitlab_permission:
            return True
        else:
            return False

    def get_corresponding_gitlab_permission(self, bitbucket_permission):
        return self.bitbucket_to_gitlab_permission_map.get(bitbucket_permission)

    @staticmethod
    def user_is_in_bitbucket_users_list(bitbucket_users_list, user):
        for bitbucket_user in bitbucket_users_list:
            display_name = bitbucket_user['user']['displayName']
            if user.name_match(display_name=display_name):
                return True
        return False

    @staticmethod
    def user_is_in_gitlab_users_list(gitlab_users_list, user):
        # debug_print('user first name', user.first_name)
        # debug_print('user last name', user.last_name)
        for gitlab_user_data in gitlab_users_list:
            gitlab_name = gitlab_user_data['name']
            # debug_print('gitlab_name', gitlab_name)
            if user.name_match(display_name=gitlab_name) or user.build_user_id.lower() == gitlab_user_data['username'].lower():
                return True
        return False

    @staticmethod
    def get_bitbucket_user_data_from_bitbucket_users_list(bitbucket_users_list, first_name, last_name):
        for bitbucket_user in bitbucket_users_list:
            if User_And_Repo_Operations.name_match(bitbucket_user['user']['displayName'], first_name, last_name):
                return bitbucket_user

    # @staticmethod
    # def get_user_data_from_gitlab_users_list(users_list, first_name, last_name):
    #     for user_data in users_list:
    #         if User_And_Repo_Operations.name_match(user_data['name'], first_name, last_name):
    #             return user_data

    @staticmethod
    def get_user_data_from_gitlab_users_list(users_list, user):
        for user_data in users_list:
            if user.name_match(user_data['name']) or user.build_user_id.lower() == user_data['username']:
                return user_data

    @staticmethod
    def name_match(bitbucket_name, first_name, last_name):
        if len(bitbucket_name) <= 0 or len(first_name) <= 0 or len(last_name) <= 0:
            try:
                raise ValueError("One of the names entered is an empty string.")
            except ValueError:
                print(ValueError)
                print('Bitbucket name: ', bitbucket_name)
                print('Jenkins first name: ', first_name)
                print('Jenkins last name: ', last_name)
        if first_name.lower() in bitbucket_name.lower() and last_name.lower() in bitbucket_name.lower():
            return True
        else:
            return False

    @staticmethod
    def get_permission_from_bitbucket_user_data(user_data):
        return user_data['permission']