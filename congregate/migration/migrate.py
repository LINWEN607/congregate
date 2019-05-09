"""
Congregate - GitLab instance migration utility

Copyright (c) 2018 - GitLab
"""

import os
import json
import argparse
import urllib
import time
import requests
import urllib2
import uuid
import glob
from re import sub
from multiprocessing.dummy import Pool as ThreadPool 
from multiprocessing import Lock

import psycopg2

from helpers import api, misc_utils
from helpers import logger as log
from migration import users, groups
from aws import aws_client
from cli.stage_projects import stage_projects
from helpers import base_module as b
from migration.gitlab.importexport import gl_importexport_client as ie_client
from migration.gitlab.variables import gl_variables_client as vars_client
from migration.gitlab.users import gl_users_client as users_client
from migration.gitlab.groups import gl_groups_client as groups_client 
from migration.gitlab.projects import gl_projects_client as proj_client
from migration.mirror import mirror_client

aws = aws_client()
ie = ie_client()
mirror = mirror_client()
variables = vars_client()
users = users_client()
groups = groups_client()
projects = proj_client()

users_map = {}
groups_map = {}


def migrate_project_info():
    """
        Subsequent function to update project info AFTER import
    """
    with open("%s/data/stage.json" % b.app_path, "r") as f:
        projects = json.load(f)

    for project in projects:
        members = project["members"]
        project.pop("members")
        b.l.logger.debug("Searching for %s" % project["name"])
        new_project = api.search(b.config.parent_host, b.config.parent_token, 'projects', project['name'])
        if len(new_project) > 0:
            if new_project[0]["name"] == project["name"] and new_project[0]["namespace"]["name"] == project["namespace"]:
                root_user_present = False
                for member in members:
                    if member["id"] == b.config.parent_user_id:
                        root_user_present = True
                    new_member = {
                        "user_id": member["id"],
                        "access_level": member["access_level"]
                    }

                    try:
                        api.generate_post_request(b.config.parent_host, b.config.parent_token, "projects/%d/members" % new_project[0]["id"], json.dumps(new_member))
                    except requests.exceptions.RequestException, e:
                        b.l.logger.error(e)
                        b.l.logger.error("Member might already exist. Attempting to update access level")
                        try:
                            api.generate_put_request(b.config.parent_host, b.config.parent_token, "projects/%d/members/%d?access_level=%d" % (new_project[0]["id"], member["id"], member["access_level"]), data=None)
                        except requests.exceptions.RequestException, e:
                            b.l.logger.error(e)
                            b.l.logger.error("Attempting to update existing member failed")

                if not root_user_present:
                    b.l.logger.info("removing root user from project")
                    api.generate_delete_request(b.config.parent_host, b.config.parent_token, "projects/%d/members/%d" % (new_project[0]["id"], b.config.parent_user_id))

def migrate_single_project_info(project, id):
    """
        Subsequent function to update project info AFTER import
    """
    members = project["members"]
    project.pop("members")
    b.l.logger.info("Searching for %s" % project["name"])
    if id is None:
        new_project = api.search(b.config.parent_host, b.config.parent_token, 'projects', project['name'])
        b.l.logger.info(new_project)
        if isinstance(new_project, dict):
            if len(new_project) > 0:
                if new_project["name"] == project["name"] and new_project["namespace"]["name"] == project["namespace"]:
                    id = new_project["id"]
        elif isinstance(new_project, list):
            if len(new_project) > 0:
                if new_project[0]["name"] == project["name"] and new_project[0]["namespace"]["name"] == project["namespace"]:
                    id = new_project[0]["id"]
    root_user_present = False
    for member in members:
        if member["id"] == b.config.parent_user_id:
            root_user_present = True
        new_member = {
            "user_id": member["id"],
            "access_level": member["access_level"]
        }

        try:
            api.generate_post_request(b.config.parent_host, b.config.parent_token, "projects/%d/members" % id, json.dumps(new_member))
        except requests.exceptions.RequestException, e:
            b.l.logger.error(e)
            b.l.logger.error("Member might already exist. Attempting to update access level")
            try:
                api.generate_put_request(b.config.parent_host, b.config.parent_token, "projects/%d/members/%d?access_level=%d" % (id, member["id"], member["access_level"]), data=None)
            except requests.exceptions.RequestException, e:
                b.l.logger.error(e)
                b.l.logger.error("Attempting to update existing member failed")

    if not root_user_present:
        b.l.logger.info("removing root user from project")
        api.generate_delete_request(b.config.parent_host, b.config.parent_token, "projects/%d/members/%d" % (id, b.config.parent_user_id))

def migrate_projects(project_json):
    if isinstance(project_json, str):
        project_json = json.loads(project_json)
    b.l.logger.debug("Searching for existing %s" % project_json["name"])
    project_exists = False
    search_response = api.generate_get_request(b.config.parent_host, b.config.parent_token, 'projects', params={'search': project_json['name']}).json()
    if len(search_response) > 0:
        for proj in search_response:
            if proj["name"] == project_json["name"] and project_json["namespace"] in proj["namespace"]["path"]:
                b.l.logger.info("Project already exists. Skipping %s" % project_json["name"])
                project_exists = True
                break
    if not project_exists:
        b.l.logger.info("%s could not be found in parent instance. Commencing project migration." % project_json["name"])
        ie.export_project(project_json)
        exported = False
        total_time = 0
        while not exported:
            response = api.generate_get_request(b.config.child_host, b.config.child_token, "projects/%d/export" % project_json["id"])
            if response.status_code == 200:
                response = response.json()
                if response["export_status"] == "finished":
                    b.l.logger.info("%s has finished exporting" % project_json["name"])
                    exported = True
                elif response["export_status"] == "failed":
                    b.l.logger.error("Export failed for %s" % project_json["name"])
                    break
                else:
                    b.l.logger.info("Waiting on %s to export" % project_json["name"])
                    if total_time < 15:
                        total_time += 1
                        time.sleep(1)
                    #elif total_time < 300:
                    #    total_time += 5
                    #    time.sleep(5)
                    #elif total_time < 3000:
                    #    total_time += 10
                    #    time.sleep(10)
                    else:
                        b.l.logger.info("Time limit exceeded")
                        break
                        #total_time += 5
                        #time.sleep(5)
            else:
                b.l.logger.info("Project cannot be found. Exiting export attempt")
                exported = False
                break
        if exported:
            #import_id = import_project(project_json)
            #if import_id is not None:
            #    migrate_variables(import_id, project_json["id"])
            #    migrate_single_project_info(project_json)
            migrate_given_export(project_json)

def migrate_given_export(project_json):
    path = "%s/%s" % (project_json["namespace"], project_json["name"])
    results = {
        path: False
    }
    if isinstance(project_json, str):
        project_json = json.loads(project_json)
    b.l.logger.debug("Searching for existing %s" % project_json["name"])
    project_exists = False
    project_id = None
    try:
        search_response = api.generate_get_request(b.config.parent_host, b.config.parent_token, 'projects', params={'search': project_json['name']}).json()
        if len(search_response) > 0:
            for proj in search_response:
                if proj["name"] == project_json["name"] and project_json["namespace"] in proj["namespace"]["path"]:
                    b.l.logger.info("Project already exists. Skipping %s" % project_json["name"])
                    project_exists = True
                    project_id = proj["id"]
                    break
        if project_id:
            import_check = api.generate_get_request(b.config.parent_host, b.config.parent_token, "projects/%d/import" % project_id).json()
            if import_check["import_status"] == "finished":
                b.l.logger.info("%s already imported" % project_json["name"])
            elif import_check["import_status"] == "scheduled":
                b.l.logger.info("%s import already scheduled" % project_json["name"])
            elif import_check["import_status"] == "started":
                b.l.logger.info("%s import already started" % project_json["name"])
            elif import_check["import_status"] == "failed":
                b.l.logger.info("%s import failed" % project_json["name"])
            elif import_check["import_status"] == "none":
                b.l.logger.info("%s import not found" % project_json["name"])
        if not project_exists:
            b.l.logger.info("Importing %s" % project_json["name"])
            import_id = ie.import_project(project_json)
            b.l.logger.info(import_id)
            if import_id is not None:
                b.l.logger.info("Unarchiving project")
                projects.unarchive_project(b.config.child_host, b.config.child_token, project_json["id"])
                b.l.logger.info("Migrating variables")
                variables.migrate_variables(import_id, project_json["id"], "project")
                b.l.logger.info("Migrating project info")
                migrate_single_project_info(project_json, import_id)
                # b.l.logger.info("Archiving project")
                # archive_project(b.config.child_host, b.config.child_token, project_json["id"])
                results[path] = True
    except requests.exceptions.RequestException, e:
        b.l.logger.error(e)
    except KeyError, e:
        b.l.logger.error(e)
        raise KeyError("Something broke in migrate_given_export")
    except OverflowError, e:
        b.l.logger.error(e)
    return results
        

def init_pool(l):
    global lock
    lock = l

def start_multi_thead(function, iterable):
    l = Lock()
    pool = ThreadPool(initializer=init_pool, initargs=(l,), processes=b.config.threads)
    pool.map(function, iterable)
    pool.close()
    pool.join()

def migrate(threads=None):
    if threads is not None:
        b.config.threads = threads
    if b.config.external_source != False:
        with open("%s" % b.config.repo_list, "r") as f:
            repo_list = json.load(f)
        start_multi_thead(handle_bitbucket_migration, repo_list)
            
    else:
        with open("%s/data/stage.json" % b.app_path, "r") as f:
            files = json.load(f)
        with open("%s/data/staged_groups.json" % b.app_path, "r") as f:
            groups_file = json.load(f)

        b.l.logger.info("Migrating user info")
        new_users = users.migrate_user_info()

        with open("%s/data/new_user_ids.txt" % b.app_path, "w") as f:
            for new_user in new_users:
                f.write("%s\n" % new_user)

        if len(new_users) > 0:
            users.update_user_info(new_users)
        else:
            users.update_user_info(new_users, overwrite=False)
        
        if len(groups_file) > 0:
            b.l.logger.info("Migrating group info")
            groups.migrate_group_info()
        else:
            b.l.logger.info("No groups to migrate")

        if len(files) > 0:
            b.l.logger.info("Migrating project info")
            pool = ThreadPool(b.config.threads)
            results = pool.map(handle_migrating_file, files)
            pool.close()
            pool.join()

            b.l.logger.info("Importing projects")
            import_pool = ThreadPool(b.config.threads)
            results = import_pool.map(migrate_given_export, files)
            b.l.logger.info("### Results ###")
            print json.dumps(results, indent=4)
            import_pool.close()
            import_pool.join()

            migrate_project_info()
        else:
            b.l.logger.info("No projects to migrate")

def kick_off_import():
    with open("%s/data/stage.json" % b.app_path, "r") as f:
        files = json.load(f)
    if len(files) > 0:
        b.l.logger.info("Importing projects")
        pool = ThreadPool(b.config.threads)
        # Open the urls in their own threads
        # and return the results
        results = pool.map(migrate_given_export, files)
        #close the pool and wait for the work to finish
        b.l.logger.info("### Results ###")
        print json.dumps(results, indent=4)
        pool.close()
        pool.join()

        #migrate_project_info()
    else:
        b.l.logger.info("No projects to migrate")

def handle_migrating_file(f):
    name = f["name"]
    id = f["id"]
    namespace = f["namespace"]
    try:
        if b.config.parent_id is not None and f["project_type"] != "user":
            parent_namespace = api.generate_get_request(b.config.parent_host, b.config.parent_token, "groups/%d" % b.config.parent_id).json()
            namespace = "%s/%s" % (parent_namespace["path"], f["namespace"])
        else:
            namespace = f["namespace"]
        if b.config.location == "filesystem":
            ie.export_import_thru_filesystem(id, name, namespace)
            #migrate_project_info()

        elif b.config.location.lower() == "filesystem-aws":
            ie.export_import_thru_fs_aws(id, name, namespace)

        elif (b.config.location).lower() == "aws":
            b.l.logger.info("Exporting %s to S3" % name)
            migrate_projects(f)
    except IOError, e:
        b.l.logger.error(e)

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
        b.l.logger.info("Searching for project %s" % repo["name"])
        search_name = repo["web_repo_url"]
        search_name = search_name.split(".git")[0]
        search_name = search_name.split("~")[0]
        if len(search_name) > 0:
            try:
                project_exists = json.load(api.generate_get_request(b.config.parent_host, b.config.parent_token, "projects?search=%s" % urllib.quote(repo["name"])))
                for proj in project_exists:
                    with_group = ("%s/%s" % (repo["group"].replace(" ", "_"), repo["name"].replace(" ", "-"))).lower()
                    pwn = proj["path_with_namespace"]
                    if proj.get("path_with_namespace", None) == search_name or pwn.lower() == with_group:
                        b.l.logger.info("Found project %s" % with_group)
                        project_id = proj["id"]
                        break
                if project_id is None:
                    b.l.logger.info("Couldn't find %s. Creating it now." % search_name)
                if repo.get("group", None) is not None or repo.get("project", None) is not None:
                    if repo.get("web_repo_url", None) is None:
                        repo["web_repo_url"] = repo["links"]["clone"][0]["href"]
                    if "~" in repo.get("web_repo_url", ""):
                        personal_repo = True
                        b.l.logger.info("Searching for personal project")
                        cat_users = repo["project_users"] + repo["repo_users"]
                        if len(cat_users) > 0:
                            user_id = None
                            for user in cat_users:
                                if len(user["email"]) > 0:
                                    user_search = json.load(api.generate_get_request(b.config.parent_host, b.config.parent_token, "users?search=%s" % urllib.quote(user["email"])))
                                    if len(user_search) > 0:
                                        b.l.logger.info("Found %s: %s" % (user_search[0]["id"], user_search[0]["email"]))
                                        user_id = user_search[0]["id"]
                                        user_name = user_search[0]["email"].split("@")[0]
                                        lock.acquire()
                                        users_map[user_name] = user_search[0]["id"]
                                        lock.release()
                                        # personal_repo = True
                                    else:
                                        if len(user["email"]) > 0:
                                            user_name = user["email"].split("@")[0]
                                            if users_map.get(user_name, None) is None:
                                                new_user_data = {
                                                    "email": user["email"],
                                                    "skip_confirmation": True,
                                                    "username": user["name"],
                                                    "name": user["displayName"],
                                                    "password": uuid.uuid4().hex
                                                }
                                                b.l.logger.info("Creating new user %s" % user["email"])
                                                created_user = json.load(api.generate_post_request(b.config.parent_host, b.config.parent_token, "users", json.dumps(new_user_data)))
                                                # b.l.logger.info(json.dumps(created_user, indent=4))
                                                user_id = created_user["id"]
                                                # personal_repo = True
                                            else:
                                                lock.acquire()
                                                group_id = users_map[user_name]
                                                lock.release()
                                                new_user_email_data = {
                                                    "email": user["email"],
                                                    "skip_confirmation": True,
                                                }
                                                b.l.logger.info("Adding new email to user %s" % user["email"])
                                                created_user = json.load(api.generate_post_request(b.config.parent_host, b.config.parent_token, "users/%s/emails" % group_id, json.dumps(new_user_email_data)))
                                                # b.l.logger.info(json.dumps(created_user, indent=4))
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
                        b.l.logger.info("Searching for existing group '%s'" % group_name)
                        group_search = json.load(api.generate_get_request(b.config.parent_host, b.config.parent_token, "groups?search=%s" % urllib.quote(group_name)))
                        for group in group_search:
                            if group["path"] == group_name:
                                b.l.logger.info("Found %s" % group_name)
                                group_id = group["id"]
                            
                        if group_id is None:
                            group_path = group_name.replace(" ", "_")
                            group_data = {
                                "name": group_name,
                                "path": group_path,
                                "visibility": "private"
                            }
                            b.l.logger.info("Creating new group %s" % group_name)
                            new_group = json.load(api.generate_post_request(b.config.parent_host, b.config.parent_token, "groups", json.dumps(group_data)))
                            group_id = new_group["id"]

                    if len(repo["project_users"]) > 0 and groups_map.get(group_id, None) is None:
                        members_already_added = groups_map.get(group_id, False)
                        if not members_already_added:
                            for user in repo["project_users"]:
                                user_id = None
                                if user.get("email", None) is not None:
                                    if len(user["email"]) > 0:
                                        user_data = None
                                        b.l.logger.info("Searching for existing user '%s'" % user["email"])
                                        user_search = json.load(api.generate_get_request(b.config.parent_host, b.config.parent_token, "users?search=%s" % urllib.quote(user["email"])))
                                        if len(user_search) > 0:
                                            b.l.logger.info("Found %s" % user_search[0]["email"])
                                            user_data = {
                                                "user_id": user_search[0]["id"],
                                                "access_level": bitbucket_permission_map[user["permission"]]
                                            }
                                            user_name = user_search[0]["email"].split("@")[0]
                                            lock.acquire()
                                            users_map[user_name] = user_search[0]["id"]
                                            lock.release()
                                            user_id = user_search[0]["id"]
                                        else:
                                            if len(user["email"]) > 0:
                                                user_name = user["email"].split("@")[0]
                                                if users_map.get(user_name, None) is None:
                                                    new_user_data = {
                                                        "email": user["email"],
                                                        "skip_confirmation": True,
                                                        "username": user["name"],
                                                        "name": user["displayName"],
                                                        "password": uuid.uuid4().hex
                                                    }
                                                    b.l.logger.info("Creating new user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(b.config.parent_host, b.config.parent_token, "users", json.dumps(new_user_data)))
                                                    b.l.logger.info(json.dumps(created_user, indent=4))
                                                    # personal_repo = True
                                                else:
                                                    new_user_email_data = {
                                                        "email": user["email"],
                                                        "skip_confirmation": True,
                                                    }
                                                    b.l.logger.info("Adding new email to user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(b.config.parent_host, b.config.parent_token, "users/%s/emails" % user_id, json.dumps(new_user_email_data)))
                                                    b.l.logger.info(json.dumps(created_user, indent=4))
                                                    # personal_repo = True
                                                user_data = {
                                                    "user_id": created_user["id"],
                                                    "access_level": bitbucket_permission_map[user["permission"]]
                                                }
                                        b.l.logger.info("%d: %s" % (group_id, groups_map.get(group_id, None)))
                                        if user_data is not None and personal_repo is False and members_already_added is False:
                                            try:
                                                b.l.logger.info("Adding %s to group" % user["email"])
                                                api.generate_post_request(b.config.parent_host, b.config.parent_token, "groups/%d/members" % group_id, json.dumps(user_data))
                                            except urllib2.HTTPError, e:
                                                b.l.logger.error("Failed to add %s to group" % user["email"])
                                                b.l.logger.error(e)
                                                b.l.logger.error(e.read())
                                else:
                                    b.l.logger.info("Empty email. Skipping %s" % user.get("name", None))
                            lock.acquire()
                            groups_map[group_id] = True
                            lock.release()
                        else:
                            b.l.logger.info("Members already exist")

                    repo["namespace_id"] = group_id
                    #Removing any trace of a tilde in the project name
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
                                        b.l.logger.info("Searching for existing user '%s'" % user["email"])
                                        user_search = json.load(api.generate_get_request(b.config.parent_host, b.config.parent_token, "users?search=%s" % urllib.quote(user["email"])))
                                        if len(user_search) > 0:
                                            user_data = {
                                                "user_id": user_search[0]["id"],
                                                "access_level": bitbucket_permission_map[user["permission"]]
                                            }
                                            user_name = user_search[0]["email"].split("@")[0]
                                            lock.acquire()
                                            users_map[user_name] = user_search[0]["id"]
                                            lock.release()
                                        else:
                                            if len(user["email"]) > 0:
                                                user_name = user["email"].split("@")[0]
                                                if users_map.get(user_name, None) is None:
                                                    new_user_data = {
                                                        "email": user["email"],
                                                        "skip_confirmation": True,
                                                        "username": user["name"],
                                                        "name": user["displayName"],
                                                        "password": uuid.uuid4().hex
                                                    }
                                                    b.l.logger.info("Creating new user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(b.config.parent_host, b.config.parent_token, "users", json.dumps(new_user_data)))
                                                    b.l.logger.info(json.dumps(created_user, indent=4))
                                                    personal_repo = True
                                                else:
                                                    new_user_email_data = {
                                                        "email": user["email"],
                                                        "skip_confirmation": True,
                                                    }
                                                    b.l.logger.info("Adding new email to user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(b.config.parent_host, b.config.parent_token, "users/%s/emails" % group_id, json.dumps(new_user_email_data)))
                                                    b.l.logger.info(json.dumps(created_user, indent=4))
                                                    personal_repo = True
                                                user_data = {
                                                    "user_id": created_user["id"],
                                                    "access_level": bitbucket_permission_map[user["permission"]]
                                                }
                                        if user_data is not None:
                                            try:
                                                b.l.logger.info("Adding %s to project" % user["email"])
                                                api.generate_post_request(b.config.parent_host, b.config.parent_token, "projects/%d/members" % project_id, json.dumps(user_data))
                                            except urllib2.HTTPError, e:
                                                b.l.logger.error("Failed to add %s to project" % user["email"])
                                                b.l.logger.error(e)
                                                b.l.logger.error(e.read())
                                        else:
                                            b.l.logger.info("No user data found")
                    else:
                        b.l.logger.info("Namespace ID null. Ignoring %s" % repo["name"])

                else:
                    b.l.logger.info("Invalid JSON found. Ignoring object")
            except urllib2.HTTPError, e:
                b.l.logger.error(e)
                b.l.logger.error(e.read())

def find_unimported_projects():
    unimported_projects = []
    with open("%s/data/project_json.json" % b.app_path, "r") as f:
        files = json.load(f)
    if len(files) > 0:
        for project_json in files:
            try:
                b.l.logger.debug("Searching for existing %s" % project_json["name"])
                project_exists = False
                search_response = api.generate_get_request(b.config.parent_host, b.config.parent_token, 'projects', params={'search': project_json['name']}).json()
                if len(search_response) > 0:
                    for proj in search_response:
                        if proj["name"] == project_json["name"]:
                            if project_json["namespace"]["full_path"].lower() == proj["path_with_namespace"].lower():
                                project_exists = True
                                break
                if not project_exists:
                    b.l.logger.info("Recording %s" % project_json["name"])
                    unimported_projects.append("%s/%s" % (project_json["namespace"], project_json["name"]))
            except IOError, e:
                b.l.logger.error(e)

    if len(unimported_projects) > 0:
        with open("%s/data/unimported_projects.txt" % b.app_path, "w") as f:
            for project in unimported_projects:
                f.writelines(project + "\n")
        print "Found %d unimported projects" % len(unimported_projects)

def remove_all_mirrors():
        # if os.path.isfile("%s/data/new_ids.txt" % b.app_path):
        #     ids = []
        #     with open("%s/data/new_ids.txt" % b.app_path, "r") as f:
        #         for line in f:
        #             ids.append(int(line.split("\n")[0]))
        # else:
        ids = get_new_ids()
        for i in ids:
            mirror.remove_mirror(i)

def get_new_ids():
    with open("%s/data/stage.json" % b.app_path, "r") as f:
        files = json.load(f)
    ids = []
    if len(files) > 0:
        for project_json in files:
            try:
                b.l.logger.debug("Searching for existing %s" % project_json["name"])
                search_response = api.generate_get_request(b.config.parent_host, b.config.parent_token, 'projects', params={'search': project_json['name']}).json()
                if len(search_response) > 0:
                    for proj in search_response:
                        if proj["name"] == project_json["name"]:

                            if "%s" % project_json["namespace"].lower() in proj["path_with_namespace"].lower():
                                print project_json["namespace"]
                                print proj["namespace"]["name"]
                                if project_json["namespace"].lower() == proj["namespace"]["name"].lower():
                                    print "adding %s/%s" % (project_json["namespace"], project_json["name"])
                                    #b.l.logger.info("Migrating variables for %s" % proj["name"])
                                    ids.append(proj["id"])
                                    break
            except IOError, e:
                b.l.logger.error(e)
        return ids

def enable_mirror():
    with open("%s/data/stage.json" % b.app_path, "r") as f:
        files = json.load(f)
    ids = get_new_ids()
    if len(files) > 0:
        for i in range(len(files)):
            id = ids[i]
            project = files[i]
            mirror.mirror_repo(project, id)


def check_visibility():
    count = 0
    if os.path.isfile("%s/data/new_ids.txt" % b.app_path):
        ids = []
        with open("%s/data/new_ids.txt" % b.app_path, "r") as f:
            for line in f:
                ids.append(int(line.split("\n")[0]))
    else:
        ids = get_new_ids()
    for i in ids:
        project = api.generate_get_request(b.config.parent_host, b.config.parent_token, "projects/%d" % i).json()
        if project["visibility"] != "private":
            print "%s, %s" % (project["path_with_namespace"], project["visibility"])
            count += 1
            data = {
                "visibility": "private"
            }
            change = api.generate_put_request(b.config.parent_host, b.config.parent_token, "projects/%d?visibility=private" % int(i), data=None)
            print change

    print count

def set_default_branch():
    for project in api.list_all(b.config.parent_host, b.config.parent_token, "projects"):
        if project.get("default_branch", None) != "master":
            id = project["id"]
            name = project["name"]
            print "Setting default branch to master for project %s" % name
            resp = api.generate_put_request(b.config.parent_host, b.config.parent_token, "projects/%d?default_branch=master" % id, data=None)
            print "Status: %d" % resp.status_code

def update_diverging_branch():
    for project in api.list_all(b.config.parent_host, b.config.parent_token, "projects"):
        if project.get("mirror_overwrites_diverged_branches", None) != True:
            id = project["id"]
            name = project["name"]
            print "Setting mirror_overwrites_diverged_branches to true for project %s" % name
            resp = api.generate_put_request(b.config.parent_host, b.config.parent_token, "projects/%d?mirror_overwrites_diverged_branches=true" % id, data=None)
            print "Status: %d" % resp.status_code

def get_total_migrated_count():
    group_projects = api.get_count(b.config.parent_host, b.config.parent_token, "groups/%d/projects" % b.config.parent_id)
    subgroup_count = 0
    for group in api.list_all(b.config.parent_host, b.config.parent_token, "groups/%d/subgroups" % b.config.parent_id):
        count = api.get_count(b.config.parent_host, b.config.parent_token, "groups/%d/projects" % group["id"])
        sub_count = 0
        if group.get("child_ids", None) is not None:
            for child_id in group["child_ids"]:
                sub_count += api.get_count(b.config.parent_host, b.config.parent_token, "groups/%d/projects" % child_id)
        subgroup_count += count
    # return subgroup_count + group_projects
    return subgroup_count

def dedupe_imports():
    with open("%s/data/unimported_projects.txt" % b.app_path, "r") as f:
        projects = f.read()
    projects = projects.split("\n")
    dedupe = set(projects)
    print len(dedupe)

def stage_unimported_projects():
    ids = []
    with open("%s/data/unimported_projects.txt" % b.app_path, "r") as f:
        projects = f.read()
    with open("%s/data/project_json.json" % b.app_path, "r") as f:
        available_projects = json.load(f)
    rewritten_projects = {}
    for i in range(len(available_projects)):
        new_obj = available_projects[i]
        id_num = available_projects[i]["path"]
        rewritten_projects[id_num] = new_obj

    projects = projects.split("\n")
    for p in projects:
        if len(p) > 0:
            if rewritten_projects.get(p.split("/")[1], None) is not None:
                ids.append(rewritten_projects.get(p.split("/")[1])["id"])
    if len(ids) > 0:
        stage_projects(ids)

def update_db(db_values):
    conn = psycopg2.connect(
        host=os.getenv('db_host_name'),
        dbname=os.getenv('db_name'),
        user=os.getenv('db_username'),
        password=os.getenv('db_password'))
    conn.autocommit = True
    print("[DEBUG] Inserting into database table")
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO ondemandmigration.gitlab_project(projectid, projectname) VALUES (%s, %s);""",
        (db_values['projectid'], db_values['projectname']))
    cur.close()
    conn.close()
    return json.dumps(db_values)

def generate_instance_map():
    for project in api.list_all(b.config.parent_host, b.config.parent_token, "projects"):
        if project.get("import_url", None) is not None:
            import_url = sub('//.+:.+@', '//', project["import_url"])
            with open("new_repomap.txt", "ab") as f:
                f.write("%s\t%s\n" % (import_url, project["id"]))



def count_unarchived_projects():
    unarchived_projects = []
    for project in api.list_all(b.config.child_host, b.config.child_token, "projects"):
        if project.get("archived", None) is not None:
            if project["archived"] == False:
                unarchived_projects.append(project["name_with_namespace"])

    print unarchived_projects
    print len(unarchived_projects)

def find_empty_repos():
    empty_repos = []
    for project in api.list_all(b.config.parent_host, b.config.parent_token, "projects?statistics=true"):
        if project.get("statistics", None) is not None:
            if project["statistics"]["repository_size"] == 0:
                b.l.logger.info("Empty repo found")
                search_response = api.search(b.config.child_host, b.config.child_token, 'projects?statistics=true', project['name'])
                if len(search_response) > 0:
                    for proj in search_response:
                        if proj["name"] == project["name"] and project["namespace"]["path"] in proj["namespace"]["path"]:
                            b.l.logger.info("Found project")
                            if proj.get("statistics", None) is not None:
                                if proj["statistics"]["repository_size"] == 0:
                                    b.l.logger.info("Project is empty in source instance. Ignoring")
                                else:
                                    empty_repos.append(project["name_with_namespace"])
    
    print empty_repos
    print len(empty_repos)
                
