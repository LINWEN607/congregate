from urllib import quote, quote_plus
from uuid import uuid4
from requests.exceptions import RequestException
import json

from helpers import base_module as b
from helpers import api
from migration.mirror import MirrorClient

users_map = {}
groups_map = {}

mirror = MirrorClient()

# TODO: decouple this as much as possible


def handle_bitbucket_migration(repo):
    bitbucket_permission_map = {
        "PROJECT_ADMIN": 50,
        "PROJECT_WRITE": 30,
        "PROJECT_READ": 20,
        "REPO_ADMIN": 40,
        "REPO_WRITE": 30,
        "REPO_READ": 20
    }
    project_id = None
    group_id = None
    personal_repo = False
    # searching for project
    if len(repo["name"]) > 0:
        b.log.info("Searching for project %s" % repo["name"])
        search_name = repo["web_repo_url"]
        search_name = search_name.split(".git")[0]
        search_name = search_name.split("~")[0]
        if len(search_name) > 0:
            try:
                project_exists = json.load(api.generate_get_request(
                    b.config.parent_host, b.config.parent_token, "projects?search=%s" % quote(repo["name"])))
                for proj in project_exists:
                    with_group = (
                        "%s/%s" % (repo["group"].replace(" ", "_"), repo["name"].replace(" ", "-"))).lower()
                    pwn = proj["path_with_namespace"]
                    if proj.get("path_with_namespace", None) == search_name or pwn.lower() == with_group:
                        b.log.info("Found project %s" % with_group)
                        project_id = proj["id"]
                        break
                if project_id is None:
                    b.log.info("Couldn't find %s. Creating it now." %
                               search_name)
                if repo.get("group", None) is not None or repo.get("project", None) is not None:
                    if repo.get("web_repo_url", None) is None:
                        repo["web_repo_url"] = repo["links"]["clone"][0]["href"]
                    if "~" in repo.get("web_repo_url", ""):
                        personal_repo = True
                        b.log.info("Searching for personal project")
                        cat_users = repo["project_users"] + repo["repo_users"]
                        if len(cat_users) > 0:
                            user_id = None
                            for user in cat_users:
                                if len(user["email"]) > 0:
                                    user_search = json.load(api.generate_get_request(
                                        b.config.parent_host, b.config.parent_token, "users?search=%s" % quote(user["email"])))
                                    if len(user_search) > 0:
                                        b.log.info("Found %s: %s" % (
                                            user_search[0]["id"], user_search[0]["email"]))
                                        user_id = user_search[0]["id"]
                                        user_name = user_search[0]["email"].split("@")[
                                            0]
                                        # lock.acquire()
                                        users_map[user_name] = user_search[0]["id"]
                                        # lock.release()
                                        # personal_repo = True
                                    else:
                                        if len(user["email"]) > 0:
                                            user_name = user["email"].split("@")[
                                                0]
                                            if users_map.get(user_name, None) is None:
                                                new_user_data = {
                                                    "email": user["email"],
                                                    "skip_confirmation": True,
                                                    "username": user["name"],
                                                    "name": user["displayName"],
                                                    "password": uuid4().hex
                                                }
                                                b.log.info(
                                                    "Creating new user %s" % user["email"])
                                                created_user = json.load(api.generate_post_request(
                                                    b.config.parent_host, b.config.parent_token, "users", json.dumps(new_user_data)))
                                                # b.log.info(json.dumps(created_user, indent=4))
                                                user_id = created_user["id"]
                                                # personal_repo = True
                                            else:
                                                # lock.acquire()
                                                group_id = users_map[user_name]
                                                # lock.release()
                                                new_user_email_data = {
                                                    "email": user["email"],
                                                    "skip_confirmation": True,
                                                }
                                                b.log.info(
                                                    "Adding new email to user %s" % user["email"])
                                                created_user = json.load(api.generate_post_request(
                                                    b.config.parent_host, b.config.parent_token, "users/%s/emails" % group_id, json.dumps(new_user_email_data)))
                                                # b.log.info(json.dumps(created_user, indent=4))
                                                # personal_repo = True
                                    if user["permission"] == "PROJECT_ADMIN":
                                        group_id = user_id
                    else:
                        if repo.get("group", None) is not None:
                            group_name = repo["group"]
                        elif repo.get("project", None) is not None:
                            project = repo["project"]
                            group_name = project.get("key", None)
                        group_name = group_name.replace(" ", "_")
                        b.log.info(
                            "Searching for existing group '%s'" % group_name)
                        group_search = json.load(api.generate_get_request(
                            b.config.parent_host, b.config.parent_token, "groups?search=%s" % quote(group_name)))
                        for group in group_search:
                            if group["path"] == group_name:
                                b.log.info("Found %s" % group_name)
                                group_id = group["id"]

                        if group_id is None:
                            group_path = group_name.replace(" ", "_")
                            group_data = {
                                "name": group_name,
                                "path": group_path,
                                "visibility": "private"
                            }
                            b.log.info("Creating new group %s" % group_name)
                            new_group = json.load(api.generate_post_request(
                                b.config.parent_host, b.config.parent_token, "groups", json.dumps(group_data)))
                            group_id = new_group["id"]

                    if len(repo["project_users"]) > 0 and groups_map.get(group_id, None) is None:
                        members_already_added = groups_map.get(group_id, False)
                        if not members_already_added:
                            for user in repo["project_users"]:
                                user_id = None
                                if user.get("email", None) is not None:
                                    if len(user["email"]) > 0:
                                        user_data = None
                                        b.log.info(
                                            "Searching for existing user '%s'" % user["email"])
                                        user_search = json.load(api.generate_get_request(
                                            b.config.parent_host, b.config.parent_token, "users?search=%s" % quote(user["email"])))
                                        if len(user_search) > 0:
                                            b.log.info("Found %s" %
                                                       user_search[0]["email"])
                                            user_data = {
                                                "user_id": user_search[0]["id"],
                                                "access_level": bitbucket_permission_map[user["permission"]]
                                            }
                                            user_name = user_search[0]["email"].split("@")[
                                                0]
                                            # lock.acquire()
                                            users_map[user_name] = user_search[0]["id"]
                                            # lock.release()
                                            user_id = user_search[0]["id"]
                                        else:
                                            if len(user["email"]) > 0:
                                                user_name = user["email"].split("@")[
                                                    0]
                                                if users_map.get(user_name, None) is None:
                                                    new_user_data = {
                                                        "email": user["email"],
                                                        "skip_confirmation": True,
                                                        "username": user["name"],
                                                        "name": user["displayName"],
                                                        "password": uuid4().hex
                                                    }
                                                    b.log.info(
                                                        "Creating new user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(
                                                        b.config.parent_host, b.config.parent_token, "users", json.dumps(new_user_data)))
                                                    b.log.info(json.dumps(
                                                        created_user, indent=4))
                                                    # personal_repo = True
                                                else:
                                                    new_user_email_data = {
                                                        "email": user["email"],
                                                        "skip_confirmation": True,
                                                    }
                                                    b.log.info(
                                                        "Adding new email to user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(
                                                        b.config.parent_host, b.config.parent_token, "users/%s/emails" % user_id, json.dumps(new_user_email_data)))
                                                    b.log.info(json.dumps(
                                                        created_user, indent=4))
                                                    # personal_repo = True
                                                user_data = {
                                                    "user_id": created_user["id"],
                                                    "access_level": bitbucket_permission_map[user["permission"]]
                                                }
                                        b.log.info("%d: %s" % (
                                            group_id, groups_map.get(group_id, None)))
                                        if user_data is not None and personal_repo is False and members_already_added is False:
                                            try:
                                                b.log.info(
                                                    "Adding %s to group" % user["email"])
                                                api.generate_post_request(
                                                    b.config.parent_host, b.config.parent_token, "groups/%d/members" % group_id, json.dumps(user_data))
                                            except RequestException, e:
                                                b.log.error(
                                                    "Failed to add %s to group" % user["email"])
                                                b.log.error(e)
                                else:
                                    b.log.info("Empty email. Skipping %s" %
                                               user.get("name", None))
                            # lock.acquire()
                            groups_map[group_id] = True
                            # lock.release()
                        else:
                            b.log.info("Members already exist")

                    repo["namespace_id"] = group_id
                    # Removing any trace of a tilde in the project name
                    repo["name"] = "".join(repo["name"].split("~"))
                    repo["personal_repo"] = personal_repo
                    if repo.get("namespace_id", None) is not None:
                        if project_id is None:
                            project_id = mirror.mirror_generic_repo(repo)
                        else:
                            if len(repo["repo_users"]) > 0:
                                for user in repo["repo_users"]:
                                    if len(user["email"]) > 0:
                                        user_data = None
                                        b.log.info(
                                            "Searching for existing user '%s'" % user["email"])
                                        user_search = json.load(api.generate_get_request(
                                            b.config.parent_host, b.config.parent_token, "users?search=%s" % quote(user["email"])))
                                        if len(user_search) > 0:
                                            user_data = {
                                                "user_id": user_search[0]["id"],
                                                "access_level": bitbucket_permission_map[user["permission"]]
                                            }
                                            user_name = user_search[0]["email"].split("@")[
                                                0]
                                            # lock.acquire()
                                            users_map[user_name] = user_search[0]["id"]
                                            # lock.release()
                                        else:
                                            if len(user["email"]) > 0:
                                                user_name = user["email"].split("@")[
                                                    0]
                                                if users_map.get(user_name, None) is None:
                                                    new_user_data = {
                                                        "email": user["email"],
                                                        "skip_confirmation": True,
                                                        "username": user["name"],
                                                        "name": user["displayName"],
                                                        "password": uuid4().hex
                                                    }
                                                    b.log.info(
                                                        "Creating new user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(
                                                        b.config.parent_host, b.config.parent_token, "users", json.dumps(new_user_data)))
                                                    b.log.info(json.dumps(
                                                        created_user, indent=4))
                                                    personal_repo = True
                                                else:
                                                    new_user_email_data = {
                                                        "email": user["email"],
                                                        "skip_confirmation": True,
                                                    }
                                                    b.log.info(
                                                        "Adding new email to user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(
                                                        b.config.parent_host, b.config.parent_token, "users/%s/emails" % group_id, json.dumps(new_user_email_data)))
                                                    b.log.info(json.dumps(
                                                        created_user, indent=4))
                                                    personal_repo = True
                                                user_data = {
                                                    "user_id": created_user["id"],
                                                    "access_level": bitbucket_permission_map[user["permission"]]
                                                }
                                        if user_data is not None:
                                            try:
                                                b.log.info(
                                                    "Adding %s to project" % user["email"])
                                                api.generate_post_request(
                                                    b.config.parent_host, b.config.parent_token, "projects/%d/members" % project_id, json.dumps(user_data))
                                            except RequestException, e:
                                                b.log.error(
                                                    "Failed to add %s to project" % user["email"])
                                                b.log.error(e)
                                        else:
                                            b.log.info("No user data found")
                    else:
                        b.log.info("Namespace ID null. Ignoring %s" %
                                   repo["name"])

                else:
                    b.log.info("Invalid JSON found. Ignoring object")
            except RequestException, e:
                b.log.error(e)
