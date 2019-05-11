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
from aws import aws_client
from cli.stage_projects import stage_projects
from helpers import base_module as b
from migration.gitlab.importexport import gl_importexport_client as ie_client
from migration.gitlab.variables import gl_variables_client as vars_client
from migration.gitlab.users import gl_users_client as users_client
from migration.gitlab.groups import gl_groups_client as groups_client 
from migration.gitlab.projects import gl_projects_client as proj_client
from migration.gitlab.pushrules import gl_pushrules_client as pushrules_client
from migration.mirror import mirror_client

from migration.bitbucket import client as bitbucket

aws = aws_client()
ie = ie_client()
mirror = mirror_client()
variables = vars_client()
users = users_client()
groups = groups_client()
projects = proj_client()
pushrules = pushrules_client()

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
    name = project["name"]
    b.l.logger.info("Searching for %s" % name)
    if id is None:
        new_project = api.search(b.config.parent_host, b.config.parent_token, 'projects', project['name'])
        b.l.logger.info(new_project)
        if isinstance(new_project, dict):
            if len(new_project) > 0:
                if new_project["name"] == name and new_project["namespace"]["name"] == project["namespace"]:
                    id = new_project["id"]
        elif isinstance(new_project, list):
            if len(new_project) > 0:
                if new_project[0]["name"] == name and new_project[0]["namespace"]["name"] == project["namespace"]:
                    id = new_project[0]["id"]
    
    projects.add_members(members, id)

    b.l.logger.info("Migrating push rules for %s" % name)
    for push_rule in pushrules.get_push_rules(project["id"], b.config.child_host, b.config.child_token):
        pushrules.add_push_rule(id, b.config.parent_host, b.config.parent_token, push_rule)
    
    b.l.logger.info("Migrating merge request approvers for %s" % name)
    # for approver in projects.get_approvals(project["id"], b.config.child_host, b.config.child_token):
    approval_data = projects.get_approvals(project["id"], b.config.child_host, b.config.child_token)
    approval_configuration = {
        "approvals_before_merge": approval_data["approvals_before_merge"],
        "reset_approvals_on_push": approval_data["reset_approvals_on_push"],
        "disable_overriding_approvers_per_merge_request": approval_data["disable_overriding_approvers_per_merge_request"]
    }
    projects.set_approval_configuration(id, b.config.parent_host, b.config.parent_token, approval_configuration)


    

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
        for proj in projects.search_for_project(b.config.parent_host, b.config.parent_token, project_json['name']):
            if proj["name"] == project_json["name"] and project_json["namespace"] in proj["namespace"]["path"]:
                b.l.logger.info("Project already exists. Skipping %s" % project_json["name"])
                project_exists = True
                project_id = proj["id"]
                break
        if project_id:
            import_check = ie.get_import_status(b.config.parent_host, b.config.parent_token, project_id).json()
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
                # projects.archive_project(b.config.child_host, b.config.child_token, project_json["id"])
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
        start_multi_thead(bitbucket.handle_bitbucket_migration, repo_list)
            
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
        results = pool.map(migrate_given_export, files)
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
            parent_namespace = groups.get_group(b.config.parent_id, b.config.parent_host, b.config.parent_token).json()
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
            exported = ie.export_import_thru_aws(id, name, namespace)
            if exported:
                #import_id = import_project(project_json)
                #if import_id is not None:
                #    migrate_variables(import_id, project_json["id"])
                #    migrate_single_project_info(project_json)
                migrate_given_export(f)
    except IOError, e:
        b.l.logger.error(e)

def find_unimported_projects():
    unimported_projects = []
    with open("%s/data/project_json.json" % b.app_path, "r") as f:
        files = json.load(f)
    if len(files) > 0:
        for project_json in files:
            try:
                b.l.logger.debug("Searching for existing %s" % project_json["name"])
                project_exists = False
                for proj in projects.search_for_project(b.config.parent_host, b.config.parent_token, project_json['name']):
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
                for proj in projects.search_for_project(b.config.parent_host, b.config.parent_token, project_json['name']):
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
        project = projects.get_project(i, b.config.parent_host, b.config.parent_token).json()
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
                for proj in api.list_all(b.config.child_host, b.config.child_token, "projects?statistics=true"):
                    if proj["name"] == project["name"] and project["namespace"]["path"] in proj["namespace"]["path"]:
                        b.l.logger.info("Found project")
                        if proj.get("statistics", None) is not None:
                            if proj["statistics"]["repository_size"] == 0:
                                b.l.logger.info("Project is empty in source instance. Ignoring")
                            else:
                                empty_repos.append(project["name_with_namespace"])
    
    print empty_repos
    print len(empty_repos)
                
