import json
from urllib import quote
from uuid import uuid4

from congregate.helpers import api, base_module as b

bitbucket_permission_map = {
    "PROJECT_ADMIN": 50,
    "PROJECT_WRITE": 30,
    "PROJECT_READ": 20,
    "REPO_ADMIN": 40,
    "REPO_WRITE": 30,
    "REPO_READ": 20
}


# Start API section

def user_search_by_email_or_name(email_or_name):
    """
    Get the user entity by email or name

    :param email_or_name: The `string` to search on
    :return: The json() of the response object returned from generate
    """
    return api.generate_get_request(
        b.config.destination_host,
        b.config.destination_token,
        "users?search=%s" % quote(email_or_name)
    ).json()


def group_search_by_name(group_name):
    """
    Get the group by name
    :param group_name: The `string` to search on
    :return: The json() of the response object returned from generate
    """
    return api.generate_get_request(
        b.config.destination_host,
        b.config.destination_token,
        "groups?search=%s" % quote(group_name)
    ).json()


def create_user(user_data):
    """
    Create a user using the passed in user data
    :param user_data:
    :return: The json() of the response object returned from the generate
    """
    return api.generate_post_request(
        b.config.destination_host,
        b.config.destination_token,
        "users",
        json.dumps(user_data)
    ).json()


def create_user_by_group(user_data, group_id):
    return api.generate_post_request(
            b.config.destination_host,
            b.config.destination_token,
            "users/%s/emails" % group_id,
            json.dumps(user_data)
        ).json()


def create_user_by_email_and_user_id(user_data, user_id):
    return api.generate_post_request(
            b.config.destination_host,
            b.config.destination_token,
            "users/%s/emails" % user_id,
            json.dumps(user_data)
        ).json()


def create_group_from_group_data(group_data):
    return api.generate_post_request(
            b.config.destination_host,
            b.config.destination_token,
            "groups",
            json.dumps(group_data)
        ).json()


def add_user_to_project(user_data, project_id):
    api.generate_post_request(
        b.config.destination_host,
        b.config.destination_token,
        "projects/%d/members" % project_id,
        json.dumps(user_data)
    )


def add_user_to_group(user_data, group_id):
    api.generate_post_request(
        b.config.destination_host,
        b.config.destination_token,
        "groups/%d/members" % group_id,
        json.dumps(user_data)
    )


# End API Section


def get_user_objects_from_user_search_and_user(user_search, user, users_map, use_email_for_user_name=False):
    user_data = {
        "user_id": user_search[0]["id"],
        "access_level": bitbucket_permission_map[user["permission"]]
    }
    if use_email_for_user_name:
        user_name = user_search[0]["email"].split("@")[0]
    else:
        user_name = user_search[0]["username"]
    users_map[user_name] = user_search[0]["id"]
    user_id = user_search[0]["id"]
    return {"user_data": user_data, "user_name": user_name, "user_id": user_id, "users_map": users_map}


def new_user_data_from_user(user):
    return {
        "email": user["email"],
        "skip_confirmation": True,
        "username": user["username"],
        "name": user["displayName"],
        "password": uuid4().hex
    }
