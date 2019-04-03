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

try:
    from helpers import conf, api, misc_utils
    from helpers import logger as log
    from migration import users, groups
    from aws import aws_client
    from cli.stage_projects import stage_projects
except ImportError:
    from congregate.helpers import conf, api, misc_utils
    from congregate.helpers import logger as log
    from congregate.migration import users, groups
    from congregate.aws import aws_client
    from congregate.cli.stage_projects import stage_projects

conf = conf.ig()

l = log.congregate_logger(__name__)

app_path = os.getenv("CONGREGATE_PATH")

parent_host = conf.parent_host
parent_token = conf.parent_token
aws = aws_client()

users_map = {}
groups_map = {}

keys_map = {}
if conf.location == "filesystem-aws":
    keys_map = aws.get_s3_keys(conf.bucket_name)

def export_project(project):
    if isinstance(project, str):
        project = json.loads(project)
    name = "%s_%s.tar.gz" % (project["namespace"], project["name"])
    presigned_put_url = aws.generate_presigned_url(name, "PUT")
    upload = [
        "upload[http_method]=PUT",
        "upload[url]=%s" % urllib.quote(presigned_put_url)
    ]

    headers = {
        'Private-Token': conf.child_token,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        api.generate_post_request(conf.child_host, conf.child_token, "projects/%d/export" % project["id"], "&".join(upload), headers=headers)
    except requests.exceptions.RequestException, e:
       pass

def import_project(project):
    """
        Imports project to parent GitLab instance. Formats users, groups, migration info(aws, filesystem) during import process
    """
    if isinstance(project, str):
        project = json.loads(project)
    name = project["name"]
    filename = "%s_%s.tar.gz" % (project["namespace"], project["name"])
    user_project = False
    if isinstance(project["members"], list):
        for member in project["members"]:
            if project["namespace"] == member["username"]:
                user_project = True
                #namespace = project["namespace"]
                new_user = api.generate_get_request(conf.parent_host, conf.parent_token, "users/%d" % member["id"]).json()
                namespace = new_user["username"]
                l.logger.info("%s is a user project belonging to %s. Attempting to import into their namespace" % (project["name"], new_user))
                break
        if not user_project:
            l.logger.info("%s is not a user project. Attempting to import into a group namespace" % (project["name"]))
            if conf.parent_id is not None:
                response = api.generate_get_request(conf.parent_host, conf.parent_token, "groups/%d" % conf.parent_id).json()
                namespace = "%s/%s" % (response["path"], project["namespace"])
            else:
                namespace = project["namespace"]
                url = project["http_url_to_repo"]
                strip = sub(r"http(s|)://.+(\.net|\.com|\.org)/", "", url)
                another_strip = strip.split("/")
                for ind, val in enumerate(another_strip):
                    if ".git" in val:
                        another_strip.pop(ind)
                full_path = "/".join(another_strip)
                l.logger.info("Searching for %s" % full_path)
                for group in api.list_all(conf.parent_host, conf.parent_token, "groups?search=%s" % project["namespace"]):
                    if group["full_path"].lower() == full_path.lower():
                        l.logger.info("Found %s" % group["full_path"])
                        namespace = group["id"]
                        break
                
        exported = False
        import_response = None
        timeout = 0
        if conf.location == "aws":
            presigned_get_url = aws.generate_presigned_url(filename, "GET")
            import_response = aws.import_from_s3(name, namespace, presigned_get_url, filename)
        elif conf.location == "filesystem-aws":
            if conf.allow_presigned_url is not None and conf.allow_presigned_url is True:
                l.logger.info("Importing %s presigned_url" % filename)
                presigned_get_url = aws.generate_presigned_url(filename, "GET")
                import_response = aws.import_from_s3(name, namespace, presigned_get_url, filename)
            else:
                l.logger.info("Copying %s to local machine" % filename)
                formatted_name = project["name"].lower()
                download = "%s_%s.tar.gz" % (project["namespace"], formatted_name)
                downloaded_filename = keys_map.get(download.lower(), None)
                if downloaded_filename is None:
                    l.logger.info("Continuing to search for filename")
                    placeholder = len(formatted_name)
                    for i in range(placeholder, 0, -1):
                        split_name = "%s_%s.tar.gz" % (
                            project["namespace"], formatted_name[:(i * (1))])
                        downloaded_filename = keys_map.get(split_name.lower(), None)
                        if downloaded_filename is not None:
                            break
                if downloaded_filename is not None:
                    import_response = aws.copy_from_s3_and_import(
                        name, namespace, downloaded_filename)

        l.logger.info(import_response)
        import_id = None
        if import_response is not None and len(import_response) > 0:
            # l.logger.info(import_response)
            import_response = json.loads(import_response)
            while not exported:
                if import_response.get("id", None) is not None:
                    import_id = import_response["id"]
                elif import_response.get("message", None) is not None:
                    if "Name has already been taken" in import_response.get("message"):
                        l.logger.debug("Searching for %s" % project["name"])
                        search_response = api.search(conf.parent_host, conf.parent_token, 'projects', project['name'])
                        if len(search_response) > 0:
                            for proj in search_response:
                                if proj["name"] == project["name"] and project["namespace"] in proj["namespace"]["path"]:
                                    l.logger.info("Found project")
                                    import_id = proj["id"]
                                    break
                        l.logger.info("Project may already exist but it cannot be found. Ignoring %s" % project["name"])
                        return None
                    elif "404 Namespace Not Found" in import_response.get("message"):
                        l.logger.info("Skipping %s. Will need to migrate later." % name)
                        import_id = None
                        break
                    elif "The project is still being deleted" in import_response.get("message"):
                        l.logger.info("Previous project export has been targeted for deletion. Skipping %s" % project["name"])
                        import_id = None
                        break
                if import_id is not None:
                    status = api.generate_get_request(conf.parent_host, conf.parent_token, "projects/%d/import" % import_id).json()
                    # l.logger.info(status)
                    if status["import_status"] == "finished":
                        l.logger.info("%s has been exported and import is occurring" % name)
                        exported = True
                        if conf.mirror_username is not None:
                            mirror_repo(project, import_id)
                    elif status["import_status"] == "failed":
                        l.logger.info("%s failed to import" % name)
                        exported = True
                else:
                    if timeout < 3600:
                        l.logger.info("Waiting on %s to upload" % name)
                        timeout += 1
                        time.sleep(1)
                    else:
                        l.logger.info("Moving on to the next project. Time limit exceeded")
                        break
    else:
        l.logger.error("Project doesn't exist. Skipping %s" % name)
        return None
    return import_id


def migrate_project_info():
    """
        Subsequent function to update project info AFTER import
    """
    with open("%s/data/stage.json" % app_path, "r") as f:
        projects = json.load(f)

    for project in projects:
        members = project["members"]
        project.pop("members")
        l.logger.debug("Searching for %s" % project["name"])
        new_project = api.search(parent_host, parent_token, 'projects', project['name'])
        if len(new_project) > 0:
            if new_project[0]["name"] == project["name"] and new_project[0]["namespace"]["name"] == project["namespace"]:
                root_user_present = False
                for member in members:
                    if member["id"] == conf.parent_user_id:
                        root_user_present = True
                    new_member = {
                        "user_id": member["id"],
                        "access_level": member["access_level"]
                    }

                    try:
                        api.generate_post_request(parent_host, parent_token, "projects/%d/members" % new_project[0]["id"], json.dumps(new_member))
                    except requests.exceptions.RequestException, e:
                        l.logger.error(e)
                        l.logger.error("Member might already exist. Attempting to update access level")
                        try:
                            api.generate_put_request(parent_host, parent_token, "projects/%d/members/%d?access_level=%d" % (new_project[0]["id"], member["id"], member["access_level"]), data=None)
                        except requests.exceptions.RequestException, e:
                            l.logger.error(e)
                            l.logger.error("Attempting to update existing member failed")

                if not root_user_present:
                    l.logger.info("removing root user from project")
                    api.generate_delete_request(parent_host, parent_token, "projects/%d/members/%d" % (new_project[0]["id"], conf.parent_user_id))

def migrate_single_project_info(project, id):
    """
        Subsequent function to update project info AFTER import
    """
    members = project["members"]
    project.pop("members")
    l.logger.info("Searching for %s" % project["name"])
    if id is None:
        new_project = api.search(parent_host, parent_token, 'projects', project['name'])
        l.logger.info(new_project)
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
        if member["id"] == conf.parent_user_id:
            root_user_present = True
        new_member = {
            "user_id": member["id"],
            "access_level": member["access_level"]
        }

        try:
            api.generate_post_request(parent_host, parent_token, "projects/%d/members" % id, json.dumps(new_member))
        except requests.exceptions.RequestException, e:
            l.logger.error(e)
            l.logger.error("Member might already exist. Attempting to update access level")
            try:
                api.generate_put_request(parent_host, parent_token, "projects/%d/members/%d?access_level=%d" % (id, member["id"], member["access_level"]), data=None)
            except requests.exceptions.RequestException, e:
                l.logger.error(e)
                l.logger.error("Attempting to update existing member failed")

    if not root_user_present:
        l.logger.info("removing root user from project")
        api.generate_delete_request(parent_host, parent_token, "projects/%d/members/%d" % (id, conf.parent_user_id))


def mirror_repo(project, import_id):
    """
        Sets up mirrored repo to allow a soft cut-over during the migration process.

        NOTE: Only works on GitLab EE instances
    """
    split_url = project["http_url_to_repo"].split("://")
    protocol = split_url[0]
    repo_url = split_url[1]
    # for member in project["members"]:
    #     if member["access_level"] >= 40:
    #         mirror_user_id = member["id"]
    #         mirror_user_name = member["username"]
    #         break

    mirror_user_name = conf.mirror_username
    mirror_user_id = conf.parent_user_id
    l.logger.info("Attempting to mirror repo")
    import_url = "%s://%s:%s@%s" % (protocol, mirror_user_name, conf.child_token, repo_url)
    l.logger.debug(import_url)
    mirror_data = {
        "mirror": True,
        "mirror_user_id": mirror_user_id,
        "import_url": import_url
    }

    response = api.generate_put_request(parent_host, parent_token, "projects/%d" % import_id, json.dumps(mirror_data))
    l.logger.info(response.text)

def mirror_generic_repo(generic_repo):
    """
        Generates shell repo with mirroring enabled by default

        NOTE: Mirroring through the API only works on GitLab EE instances
    """
    split_url = generic_repo["web_repo_url"].split("://")
    protocol = split_url[0]
    repo_url = split_url[1]
    namespace_id = int(generic_repo["namespace_id"])
    print namespace_id
    mirror_user_id = conf.parent_user_id
    user_name = conf.external_user_name
    user_password = conf.external_user_password
    
    import_url = "%s://%s:%s@%s" % (protocol, user_name, user_password, repo_url)
    l.logger.debug(import_url)
    data = {
        "name": generic_repo["name"],
        "namespace_id": namespace_id,
        "mirror": True,
        "mirror_user_id": mirror_user_id,
        "import_url": import_url,
        "only_mirror_protected_branches": False,
        "mirror_overwrites_diverged_branches": True,
        "default_branch": "master"
    }

    if generic_repo.get("visibility", None) is not None:
        data["visibility"] = generic_repo["visibility"]

    try:
        if generic_repo.get("personal_repo", None) == True:
            data.pop("namespace_id")
            data.pop("default_branch")
            data["mirror_user_id"] = namespace_id
            l.logger.info("Attempting to generate personal shell repo for %s and create mirror" % generic_repo["name"])
            # l.logger.info(json.dumps(data, indent=4))
            response = json.load(api.generate_post_request(parent_host, parent_token, "projects/user/%d" % namespace_id, json.dumps(data)))
            if response.get("id", None) is not None:
                l.logger.debug("Setting default branch to master")
                default_branch = {
                    "default_branch": "master"
                }
                api.generate_put_request(parent_host, parent_token, "projects/%d" % response["id"], json.dumps(default_branch))
        else:
            l.logger.info("Attempting to generate shell repo for %s and create mirror" % generic_repo["name"])
            response = json.load(api.generate_post_request(parent_host, parent_token, "projects", json.dumps(data)))
        #put_response = api.generate_put_request(parent_host, parent_token, "projects/%d" % response["id"], json.dumps(put_data))
        l.logger.info("Project %s has been created and mirroring has been enabled" % generic_repo["name"])
        db_data = {
            "projectname": generic_repo["web_repo_url"],
            "projectid": response["id"]
        }
        lock.acquire()
        update_db(db_data)
        lock.release()
        with open("repomap.txt", "ab") as f:
            f.write("%s\t%s\n" % (generic_repo["web_repo_url"], response["id"]))
        # l.logger.debug(response)

        return response["id"]
        #l.logger.debug(put_response.json())
    except urllib2.HTTPError, e:
        l.logger.error(e)
        l.logger.error(e.read())
        return None

def remove_mirror(project_id):
    """
        Removes repo mirror information after migration process is complete

        NOTE: Only works on GitLab EE instances
    """
    mirror_data = {
        "mirror": False,
        "mirror_user_id": None,
        "import_url": None
    }

    l.logger.info("Removing mirror from project %d" % project_id)
    api.generate_put_request(conf.parent_host, conf.parent_token, "projects/%d" % project_id, json.dumps(mirror_data))

def migrate_variables(import_id, id):
    try:
        response = api.generate_get_request(conf.child_host, conf.child_token, "projects/%d/variables" % id)
        if response.status_code == 200:
            response_json = response.json()
            if len(response_json) > 0:
                for i in range(len(response_json)):
                    appended_data = response_json[i]
                    appended_data["environment_scope"] = "*"
                    wrapped_data = json.dumps(appended_data)
                    api.generate_post_request(conf.parent_host, conf.parent_token, "projects/%d/variables" % import_id, wrapped_data)
            else:
                l.logger.info("Project does not have CI variables. Skipping.")
        else:
            l.logger.error("Response returned a %d with the message: %s" % (response.status_code, response.text))
    except requests.exceptions.RequestException, e:
        return None

def migrate_projects(project_json):
    if isinstance(project_json, str):
        project_json = json.loads(project_json)
    l.logger.debug("Searching for existing %s" % project_json["name"])
    project_exists = False
    search_response = api.generate_get_request(conf.parent_host, conf.parent_token, 'projects', params={'search': project_json['name']}).json()
    if len(search_response) > 0:
        for proj in search_response:
            if proj["name"] == project_json["name"] and project_json["namespace"] in proj["namespace"]["path"]:
                l.logger.info("Project already exists. Skipping %s" % project_json["name"])
                project_exists = True
                break
    if not project_exists:
        l.logger.info("%s could not be found in parent instance. Commencing project migration." % project_json["name"])
        export_project(project_json)
        exported = False
        total_time = 0
        while not exported:
            response = api.generate_get_request(conf.child_host, conf.child_token, "projects/%d/export" % project_json["id"])
            if response.status_code == 200:
                response = response.json()
                if response["export_status"] == "finished":
                    l.logger.info("%s has finished exporting" % project_json["name"])
                    exported = True
                elif response["export_status"] == "failed":
                    l.logger.error("Export failed for %s" % project_json["name"])
                    break
                else:
                    l.logger.info("Waiting on %s to export" % project_json["name"])
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
                        l.logger.info("Time limit exceeded")
                        break
                        #total_time += 5
                        #time.sleep(5)
            else:
                l.logger.info("Project cannot be found. Exiting export attempt")
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
    l.logger.debug("Searching for existing %s" % project_json["name"])
    project_exists = False
    project_id = None
    try:
        search_response = api.generate_get_request(conf.parent_host, conf.parent_token, 'projects', params={'search': project_json['name']}).json()
        if len(search_response) > 0:
            for proj in search_response:
                if proj["name"] == project_json["name"] and project_json["namespace"] in proj["namespace"]["path"]:
                    l.logger.info("Project already exists. Skipping %s" % project_json["name"])
                    project_exists = True
                    project_id = proj["id"]
                    break
        if project_id:
            import_check = api.generate_get_request(conf.parent_host, conf.parent_token, "projects/%d/import" % project_id).json()
            if import_check["import_status"] == "finished":
                l.logger.info("%s already imported" % project_json["name"])
            elif import_check["import_status"] == "scheduled":
                l.logger.info("%s import already scheduled" % project_json["name"])
            elif import_check["import_status"] == "started":
                l.logger.info("%s import already started" % project_json["name"])
            elif import_check["import_status"] == "failed":
                l.logger.info("%s import failed" % project_json["name"])
            elif import_check["import_status"] == "none":
                l.logger.info("%s import not found" % project_json["name"])
        if not project_exists:
            l.logger.info("Importing %s" % project_json["name"])
            import_id = import_project(project_json)
            l.logger.info(import_id)
            if import_id is not None:
                l.logger.info("Unarchiving project")
                unarchive_project(conf.child_host, conf.child_token, project_json["id"])
                l.logger.info("Migrating variables")
                migrate_variables(import_id, project_json["id"])
                l.logger.info("Migrating project info")
                migrate_single_project_info(project_json, import_id)
                # l.logger.info("Archiving project")
                # archive_project(conf.child_host, conf.child_token, project_json["id"])
                # results[path] = True
    except requests.exceptions.RequestException, e:
        l.logger.error(e)
    except KeyError, e:
        l.logger.error(e)
        raise KeyError("Something broke in migrate_given_export")
    except OverflowError, e:
        l.logger.error(e)
    return results
        

def init_pool(l):
    global lock
    lock = l

def start_multi_thead(function, iterable):
    l = Lock()
    pool = ThreadPool(initializer=init_pool, initargs=(l,), processes=4)
    pool.map(function, iterable)
    pool.close()
    pool.join()

def migrate():
    if conf.external_source != False:
        with open("%s" % conf.repo_list, "r") as f:
            repo_list = json.load(f)
        start_multi_thead(handle_bitbucket_migration, repo_list)
            
    else:
        with open("%s/data/stage.json" % app_path, "r") as f:
            files = json.load(f)
        with open("%s/data/staged_groups.json" % app_path, "r") as f:
            groups_file = json.load(f)

        l.logger.info("Migrating user info")
        new_users = users.migrate_user_info()

        with open("%s/data/new_user_ids.txt" % app_path, "w") as f:
            for new_user in new_users:
                f.write("%s\n" % new_user)

        if len(new_users) > 0:
            users.update_user_info(new_users)
        else:
            users.update_user_info(new_users, overwrite=False)
        
        if len(groups_file) > 0:
            l.logger.info("Migrating group info")
            groups.migrate_group_info()
        else:
            l.logger.info("No groups to migrate")

        if len(files) > 0:
            l.logger.info("Migrating project info")
            pool = ThreadPool(3)
            results = pool.map(handle_migrating_file, files)
            pool.close()
            pool.join()

            l.logger.info("Importing projects")
            import_pool = ThreadPool(3)
            results = import_pool.map(migrate_given_export, files)
            l.logger.info("### Results ###")
            print json.dumps(results, indent=4)
            import_pool.close()
            import_pool.join()

            #migrate_project_info()
        else:
            l.logger.info("No projects to migrate")

def kick_off_import():
    with open("%s/data/stage.json" % app_path, "r") as f:
        files = json.load(f)
    if len(files) > 0:
        l.logger.info("Importing projects")
        pool = ThreadPool(3)
        # Open the urls in their own threads
        # and return the results
        results = pool.map(migrate_given_export, files)
        #close the pool and wait for the work to finish
        l.logger.info("### Results ###")
        print json.dumps(results, indent=4)
        pool.close()
        pool.join()

        #migrate_project_info()
    else:
        l.logger.info("No projects to migrate")

def handle_migrating_file(f):
    working_dir = os.getcwd()
    name = f["name"]
    id = f["id"]
    try:
        if conf.parent_id is not None and f["project_type"] != "user":
            parent_namespace = api.generate_get_request(conf.parent_host, conf.parent_token, "groups/%d" % conf.parent_id).json()
            namespace = "%s/%s" % (parent_namespace["path"], f["namespace"])
        else:
            namespace = f["namespace"]
        if conf.location == "filesystem":
            l.logger.info("Exporting %s to %s" % (name, conf.filesystem_path))
            api.generate_post_request(conf.child_host, conf.child_token, "projects/%d/export" % id, "")
            if working_dir != conf.filesystem_path:
                os.chdir(conf.filesystem_path)
            url = "%s/api/v4/projects/%d/export/download" % (conf.child_host, id)
            filename = misc_utils.download_file(url, conf.filesystem_path, headers={"PRIVATE-TOKEN": conf.child_token})

            data = {
                "path": name,
                "file": "%s/downloads/%s" % (conf.filesystem_path, filename),
                "namespace": namespace
            }

            api.generate_post_request(conf.parent_host, conf.parent_token, "projects/import", data=data)

            #migrate_project_info()

        elif conf.location.lower() == "filesystem-aws":
            testkey = "%s_%s.tar.gz" % (f["namespace"], f["name"])
            if keys_map.get(testkey.lower(), None) is None:
                l.logger.info("Exporting %s to %s" % (name, conf.filesystem_path))
                l.logger.info("Unarchiving %s" % name)
                unarchive_project(conf.child_host, conf.child_token, id)
                api.generate_post_request(
                    conf.child_host, conf.child_token, "projects/%d/export" % id, {})
                # download = api.generate_get_request(conf.child_host, conf.child_token, "projects/%d/export/download" % id)
                url = "%s/api/v4/projects/%d/export/download" % (
                    conf.child_host, id)
                # filename = download.info().getheader("Content-Disposition").split("=")[1]
                exported = False
                total_time = 0
                while not exported:
                    response = api.generate_get_request(
                        conf.child_host, conf.child_token, "projects/%d/export" % id)
                    if response.status_code == 200:
                        response = response.json()
                        if response["export_status"] == "finished":
                            l.logger.info("%s has finished exporting" % name)
                            exported = True
                        elif response["export_status"] == "failed":
                            l.logger.error("Export failed for %s" % name)
                            break
                        else:
                            l.logger.info("Waiting on %s to export" % name)
                            if total_time < 3600:
                                total_time += 1
                                time.sleep(1)
                            else:
                                l.logger.info(
                                    "Time limit exceeded. Going to attempt to download anyway")
                                exported = True
                    else:
                        l.logger.info("Project doesn't exist. Skipping %s export" % name)
                        exported = False
                        break
                if exported:
                    l.logger.info("Downloading export")
                    path_with_namespace = "%s_%s.tar.gz" % (
                        f["namespace"], f["name"])
                    try:
                        filename = misc_utils.download_file(url, conf.filesystem_path, path_with_namespace, headers={"PRIVATE-TOKEN": conf.child_token})
                        l.logger.info("Copying %s to s3" % filename)
                        success = aws.copy_file_to_s3(filename)
                        if success:
                            l.logger.info("Removing %s from downloads" % filename)
                            filepattern = sub(
                                r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{3}_', '', filename)
                            for f in glob.glob("%s/downloads/*%s" %
                                            (conf.filesystem_path, filepattern)):
                                os.remove(f)
                            # l.logger.info("Archiving %s" % name)
                            # api.generate_post_request(
                            #     conf.child_host, conf.child_token, "projects/%d/archive" % id, {})
                    except Exception as e:
                        l.logger.error("Download or copy to S3 failed")
                        l.logger.error(e)
            else:
                l.logger.info("Export found. Skipping %s" % testkey)

        elif (conf.location).lower() == "aws":
            l.logger.info("Exporting %s to S3" % name)
            migrate_projects(f)
    except IOError, e:
        l.logger.error(e)

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
        l.logger.info("Searching for project %s" % repo["name"])
        search_name = repo["web_repo_url"]
        search_name = search_name.split(".git")[0]
        search_name = search_name.split("~")[0]
        if len(search_name) > 0:
            try:
                project_exists = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "projects?search=%s" % urllib.quote(repo["name"])))
                for proj in project_exists:
                    with_group = ("%s/%s" % (repo["group"].replace(" ", "_"), repo["name"].replace(" ", "-"))).lower()
                    pwn = proj["path_with_namespace"]
                    if proj.get("path_with_namespace", None) == search_name or pwn.lower() == with_group:
                        l.logger.info("Found project %s" % with_group)
                        project_id = proj["id"]
                        break
                if project_id is None:
                    l.logger.info("Couldn't find %s. Creating it now." % search_name)
                if repo.get("group", None) is not None or repo.get("project", None) is not None:
                    if repo.get("web_repo_url", None) is None:
                        repo["web_repo_url"] = repo["links"]["clone"][0]["href"]
                    if "~" in repo.get("web_repo_url", ""):
                        personal_repo = True
                        l.logger.info("Searching for personal project")
                        cat_users = repo["project_users"] + repo["repo_users"]
                        if len(cat_users) > 0:
                            user_id = None
                            for user in cat_users:
                                if len(user["email"]) > 0:
                                    user_search = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "users?search=%s" % urllib.quote(user["email"])))
                                    if len(user_search) > 0:
                                        l.logger.info("Found %s: %s" % (user_search[0]["id"], user_search[0]["email"]))
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
                                                l.logger.info("Creating new user %s" % user["email"])
                                                created_user = json.load(api.generate_post_request(conf.parent_host, conf.parent_token, "users", json.dumps(new_user_data)))
                                                # l.logger.info(json.dumps(created_user, indent=4))
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
                                                l.logger.info("Adding new email to user %s" % user["email"])
                                                created_user = json.load(api.generate_post_request(conf.parent_host, conf.parent_token, "users/%s/emails" % group_id, json.dumps(new_user_email_data)))
                                                # l.logger.info(json.dumps(created_user, indent=4))
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
                        l.logger.info("Searching for existing group '%s'" % group_name)
                        group_search = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "groups?search=%s" % urllib.quote(group_name)))
                        for group in group_search:
                            if group["path"] == group_name:
                                l.logger.info("Found %s" % group_name)
                                group_id = group["id"]
                            
                        if group_id is None:
                            group_path = group_name.replace(" ", "_")
                            group_data = {
                                "name": group_name,
                                "path": group_path,
                                "visibility": "private"
                            }
                            l.logger.info("Creating new group %s" % group_name)
                            new_group = json.load(api.generate_post_request(conf.parent_host, parent_token, "groups", json.dumps(group_data)))
                            group_id = new_group["id"]

                    if len(repo["project_users"]) > 0 and groups_map.get(group_id, None) is None:
                        members_already_added = groups_map.get(group_id, False)
                        if not members_already_added:
                            for user in repo["project_users"]:
                                user_id = None
                                if user.get("email", None) is not None:
                                    if len(user["email"]) > 0:
                                        user_data = None
                                        l.logger.info("Searching for existing user '%s'" % user["email"])
                                        user_search = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "users?search=%s" % urllib.quote(user["email"])))
                                        if len(user_search) > 0:
                                            l.logger.info("Found %s" % user_search[0]["email"])
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
                                                    l.logger.info("Creating new user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(conf.parent_host, conf.parent_token, "users", json.dumps(new_user_data)))
                                                    l.logger.info(json.dumps(created_user, indent=4))
                                                    # personal_repo = True
                                                else:
                                                    new_user_email_data = {
                                                        "email": user["email"],
                                                        "skip_confirmation": True,
                                                    }
                                                    l.logger.info("Adding new email to user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(conf.parent_host, conf.parent_token, "users/%s/emails" % user_id, json.dumps(new_user_email_data)))
                                                    l.logger.info(json.dumps(created_user, indent=4))
                                                    # personal_repo = True
                                                user_data = {
                                                    "user_id": created_user["id"],
                                                    "access_level": bitbucket_permission_map[user["permission"]]
                                                }
                                        l.logger.info("%d: %s" % (group_id, groups_map.get(group_id, None)))
                                        if user_data is not None and personal_repo is False and members_already_added is False:
                                            try:
                                                l.logger.info("Adding %s to group" % user["email"])
                                                api.generate_post_request(conf.parent_host, conf.parent_token, "groups/%d/members" % group_id, json.dumps(user_data))
                                            except urllib2.HTTPError, e:
                                                l.logger.error("Failed to add %s to group" % user["email"])
                                                l.logger.error(e)
                                                l.logger.error(e.read())
                                else:
                                    l.logger.info("Empty email. Skipping %s" % user.get("name", None))
                            lock.acquire()
                            groups_map[group_id] = True
                            lock.release()
                        else:
                            l.logger.info("Members already exist")

                    repo["namespace_id"] = group_id
                    #Removing any trace of a tilde in the project name
                    repo["name"] = "".join(repo["name"].split("~"))
                    repo["personal_repo"] = personal_repo
                    if repo.get("namespace_id", None) is not None:
                        if project_id is None:
                            project_id = mirror_generic_repo(repo)
                        else:
                            if len(repo["repo_users"]) > 0:
                                for user in repo["repo_users"]:
                                    if len(user["email"]) > 0:
                                        user_data = None
                                        l.logger.info("Searching for existing user '%s'" % user["email"])
                                        user_search = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "users?search=%s" % urllib.quote(user["email"])))
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
                                                    l.logger.info("Creating new user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(conf.parent_host, conf.parent_token, "users", json.dumps(new_user_data)))
                                                    l.logger.info(json.dumps(created_user, indent=4))
                                                    personal_repo = True
                                                else:
                                                    new_user_email_data = {
                                                        "email": user["email"],
                                                        "skip_confirmation": True,
                                                    }
                                                    l.logger.info("Adding new email to user %s" % user["email"])
                                                    created_user = json.load(api.generate_post_request(conf.parent_host, conf.parent_token, "users/%s/emails" % group_id, json.dumps(new_user_email_data)))
                                                    l.logger.info(json.dumps(created_user, indent=4))
                                                    personal_repo = True
                                                user_data = {
                                                    "user_id": created_user["id"],
                                                    "access_level": bitbucket_permission_map[user["permission"]]
                                                }
                                        if user_data is not None:
                                            try:
                                                l.logger.info("Adding %s to project" % user["email"])
                                                api.generate_post_request(conf.parent_host, conf.parent_token, "projects/%d/members" % project_id, json.dumps(user_data))
                                            except urllib2.HTTPError, e:
                                                l.logger.error("Failed to add %s to project" % user["email"])
                                                l.logger.error(e)
                                                l.logger.error(e.read())
                                        else:
                                            l.logger.info("No user data found")
                    else:
                        l.logger.info("Namespace ID null. Ignoring %s" % repo["name"])

                else:
                    l.logger.info("Invalid JSON found. Ignoring object")
            except urllib2.HTTPError, e:
                l.logger.error(e)
                l.logger.error(e.read())

def find_unimported_projects():
    unimported_projects = []
    with open("%s/data/project_json.json" % app_path, "r") as f:
        files = json.load(f)
    if len(files) > 0:
        for project_json in files:
            try:
                l.logger.debug("Searching for existing %s" % project_json["name"])
                project_exists = False
                search_response = api.generate_get_request(conf.parent_host, conf.parent_token, 'projects', params={'search': project_json['name']}).json()
                if len(search_response) > 0:
                    for proj in search_response:
                        if proj["name"] == project_json["name"]:
                            if project_json["namespace"]["full_path"].lower() == proj["path_with_namespace"].lower():
                                project_exists = True
                                break
                if not project_exists:
                    l.logger.info("Recording %s" % project_json["name"])
                    unimported_projects.append("%s/%s" % (project_json["namespace"], project_json["name"]))
            except IOError, e:
                l.logger.error(e)

    if len(unimported_projects) > 0:
        with open("%s/data/unimported_projects.txt" % app_path, "w") as f:
            for project in unimported_projects:
                f.writelines(project + "\n")
        print "Found %d unimported projects" % len(unimported_projects)

def migrate_variables_in_stage():
    with open("%s/data/stage.json" % app_path, "r") as f:
        files = json.load(f)
    ids = []
    project_id = None
    if len(files) > 0:
        for project_json in files:
            try:
                l.logger.debug("Searching for existing %s" % project_json["name"])
                project_exists = False
                search_response = api.generate_get_request(conf.parent_host, conf.parent_token, 'projects', params={'search': project_json['name']}).json()
                if len(search_response) > 0:
                    for proj in search_response:
                        if proj["name"] == project_json["name"]:
                            if "%s" % project_json["namespace"].lower() in proj["path_with_namespace"].lower():
                                project_exists = True
                                #l.logger.info("Migrating variables for %s" % proj["name"])
                                project_id = proj["id"]
                                ids.append(project_id)
                                break
                            else:
                                project_id = None
                if project_id is not None:
                    migrate_variables(project_id, project_json["id"])
            except IOError, e:
                l.logger.error(e)
        with open("%s/data/ids_variable.txt" % app_path, "w") as f:
            for i in ids:
                f.write("%s\n" % i)
        print len(ids)

def get_new_ids():
    with open("%s/data/stage.json" % app_path, "r") as f:
        files = json.load(f)
    ids = []
    if len(files) > 0:
        for project_json in files:
            try:
                l.logger.debug("Searching for existing %s" % project_json["name"])
                search_response = api.generate_get_request(conf.parent_host, conf.parent_token, 'projects', params={'search': project_json['name']}).json()
                if len(search_response) > 0:
                    for proj in search_response:
                        if proj["name"] == project_json["name"]:

                            if "%s" % project_json["namespace"].lower() in proj["path_with_namespace"].lower():
                                print project_json["namespace"]
                                print proj["namespace"]["name"]
                                if project_json["namespace"].lower() == proj["namespace"]["name"].lower():
                                    print "adding %s/%s" % (project_json["namespace"], project_json["name"])
                                    #l.logger.info("Migrating variables for %s" % proj["name"])
                                    ids.append(proj["id"])
                                    break
            except IOError, e:
                l.logger.error(e)
        return ids

def enable_mirror():
    with open("%s/data/stage.json" % app_path, "r") as f:
        files = json.load(f)
    ids = get_new_ids()
    if len(files) > 0:
        for i in range(len(files)):
            id = ids[i]
            project = files[i]
            mirror_repo(project, id)


def check_visibility():
    count = 0
    if os.path.isfile("%s/data/new_ids.txt" % app_path):
        ids = []
        with open("%s/data/new_ids.txt" % app_path, "r") as f:
            for line in f:
                ids.append(int(line.split("\n")[0]))
    else:
        ids = get_new_ids()
    for i in ids:
        project = api.generate_get_request(conf.parent_host, conf.parent_token, "projects/%d" % i).json()
        if project["visibility"] != "private":
            print "%s, %s" % (project["path_with_namespace"], project["visibility"])
            count += 1
            data = {
                "visibility": "private"
            }
            change = api.generate_put_request(conf.parent_host, conf.parent_token, "projects/%d?visibility=private" % int(i), data=None)
            print change

    print count

def remove_all_mirrors():
    # if os.path.isfile("%s/data/new_ids.txt" % app_path):
    #     ids = []
    #     with open("%s/data/new_ids.txt" % app_path, "r") as f:
    #         for line in f:
    #             ids.append(int(line.split("\n")[0]))
    # else:
    ids = get_new_ids()
    for i in ids:
        remove_mirror(i)

def get_total_migrated_count():
    group_projects = api.get_count(conf.parent_host, conf.parent_token, "groups/%d/projects" % conf.parent_id)
    subgroup_count = 0
    for group in api.list_all(conf.parent_host, conf.parent_token, "groups/%d/subgroups" % conf.parent_id):
        count = api.get_count(conf.parent_host, conf.parent_token, "groups/%d/projects" % group["id"])
        sub_count = 0
        if group.get("child_ids", None) is not None:
            for child_id in group["child_ids"]:
                sub_count += api.get_count(conf.parent_host, conf.parent_token, "groups/%d/projects" % child_id)
        subgroup_count += count
    # return subgroup_count + group_projects
    return subgroup_count

def dedupe_imports():
    with open("%s/data/unimported_projects.txt" % app_path, "r") as f:
        projects = f.read()
    projects = projects.split("\n")
    dedupe = set(projects)
    print len(dedupe)

def stage_unimported_projects():
    ids = []
    with open("%s/data/unimported_projects.txt" % app_path, "r") as f:
        projects = f.read()
    with open("%s/data/project_json.json" % app_path, "r") as f:
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

def set_default_branch():
    for project in api.list_all(conf.parent_host, conf.parent_token, "projects"):
        id = project["id"]
        name = project["name"]
        l.logger.info("Setting default branch to master for project %s" % name)
        api.generate_put_request(conf.parent_host, conf.parent_token, "projects/%d?default_branch=master" % id, data=None)

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
    for project in api.list_all(conf.parent_host, conf.parent_token, "projects"):
        if project.get("import_url", None) is not None:
            import_url = sub('//.+:.+@', '//', project["import_url"])
            with open("new_repomap.txt", "ab") as f:
                f.write("%s\t%s\n" % (import_url, project["id"]))

def archive_project(host, token, id):
    return api.generate_post_request(host, token, "projects/%d/archive" % id, {}).json()

def unarchive_project(host, token, id):
    return api.generate_post_request(host, token, "projects/%d/unarchive" % id, {}).json()

def count_unarchived_projects():
    unarchived_projects = []
    for project in api.list_all(conf.child_host, conf.child_token, "projects"):
        if project.get("archived", None) is not None:
            if project["archived"] == False:
                unarchived_projects.append(project["name_with_namespace"])

    print unarchived_projects
    print len(unarchived_projects)

def find_empty_repos():
    empty_repos = []
    for project in api.list_all(conf.parent_host, conf.parent_token, "projects?statistics=true"):
        if project.get("statistics", None) is not None:
            if project["statistics"]["repository_size"] == 0:
                l.logger.info("Empty repo found")
                search_response = api.search(conf.child_host, conf.child_token, 'projects?statistics=true', project['name'])
                if len(search_response) > 0:
                    for proj in search_response:
                        if proj["name"] == project["name"] and project["namespace"]["path"] in proj["namespace"]["path"]:
                            l.logger.info("Found project")
                            if proj.get("statistics", None) is not None:
                                if proj["statistics"]["repository_size"] == 0:
                                    l.logger.info("Project is empty in source instance. Ignoring")
                                else:
                                    empty_repos.append(project["name_with_namespace"])
    
    print empty_repos
    print len(empty_repos)
                

    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle project-related tasks')
    parser.add_argument('--retrieve', type=bool, default=False, dest='retrieve',
                    help='Retrieve project info and save it to %s/data/projects.json' % app_path)
    parser.add_argument('--migrate', type=bool, default=False, dest='migrate',
                    help='Migrate all project info to parent instance')
    parser.add_argument('--quiet', type=bool, default=False, dest='quiet',
                    help='Silent output of script')
    parser.add_argument('--project_json', type=str, default=None, dest='project_json',
                    help='Provide JSON of project to migrate')

    args = parser.parse_args()

    retrieve = args.retrieve
    migrate = args.migrate
    quiet = args.quiet
    project_json = args.project_json

    if retrieve:
        #retrieve_project_info()
        pass

    if migrate:
        migrate_project_info()

    if project_json:
        migrate_projects(project_json)
