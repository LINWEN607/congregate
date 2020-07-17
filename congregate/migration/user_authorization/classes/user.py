import os
import re
import logging

from urllib.parse import quote
from ..util.misc import process_name


class User(object):
    """
    A class that represents a users attributes in Bitbucket, GitLab, and the Jenkins job.
    """

    def __init__(self, first_name, last_name, email, build_user_id):
        attributes = [
            'first_name',
            'last_name',
            'email',
            'build_user_id'
        ]
        assert all([User.is_valid_attribute(attribute)
                    for attribute in attributes])
        self.first_name = process_name(name=first_name)
        self.last_name = process_name(name=last_name)
        self.email = email
        self.build_user_id = build_user_id

    @property
    def display_name(self):
        return '%s, %s' % (self.last_name, self.first_name)

    def get_gitlab_id(self, gitlab_instance):
        url_extension = '/users'
        params = {
            'search': self.email
        }
        response = gitlab_instance.api_request(
            request_type='get', url_extension=url_extension, params=params)
        response_json = response.json()
        try:
            user_id = response_json[0]["id"]
        except:
            logging.info("From get_gitlab_id function: User does not exist.")

            user_id = None
        return user_id

    def create_gitlab_user(self, gitlab_instance):
        data = {
            "name": self.display_name,
            "username": self.build_user_id,
            "email": self.email,
            "reset_password": "True"
        }
        url_extension = '/users'
        response = gitlab_instance.api_request(
            request_type='post', url_extension=url_extension, data=data)
        response_json = response.json()
        success_status_codes = [200, 201]
        if response.status_code in success_status_codes:
            user_id = response_json["id"]
            logging.info('Created user with user id %d.' % user_id)
        else:
            logging.info('Bad request in create_gitlab_user')

    def get_gitlab_username(self, gitlab_instance):
        url_extension = "/users"
        params = {
            'search': self.email
        }
        user_search = gitlab_instance.api_request(
            request_type='get', url_extension=url_extension, params=params)
        # user_search = api.generate_get_request(conf.destination_host, conf.destination_token,
        #                                                  "users?search=%s" % quote(user["email"]))
        try:
            return user_search[0]["email"].split("@")[0]
        except Exception as e:
            return None

    def name_match(self, display_name):
        """
        Checks if the users name matches the display_name
        :param display_name: A string that is expected to include the users first name and last name
        :return: True if the name matches. Otherwise False
        """
        assert display_name != None and len(
            display_name) > 0, "Invalid display_name input: {}".format(display_name)
        processed_display_name = process_name(display_name)
        conditions_for_name_match = [
            self.first_name.lower() in processed_display_name.lower(),
            self.last_name.lower() in processed_display_name.lower()
        ]
        if all(conditions_for_name_match):
            return True
        else:
            return False

    @staticmethod
    def user_exists_in_gitlab(email, gitlab_instance):
        url_extension = '/users'
        params = {
            'search': email
        }
        response = gitlab_instance.api_request(
            request_type='get', url_extension=url_extension, params=params)
        response_json = response.json()
        try:
            user_id = response_json[0]["id"]
            user_exists = True
        except:
            user_exists = False
        finally:
            return user_exists

    @staticmethod
    def is_valid_attribute(attribute):
        conditions = [
            len(attribute) > 0
        ]
        return all(conditions)
