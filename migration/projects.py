"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import json
import sys
import subprocess
import argparse
import urllib
import urllib2
import time
import logging
import requests
from multiprocessing.dummy import Pool as ThreadPool 

try:
    from helpers import conf, api, misc_utils
    from helpers import logger as log
    from migration import users, groups
    from aws.presigned import generate_presigned_url
    from aws.import_from_s3 import import_from_s3
    from cli.stage_projects import stage_projects
except ImportError:
    from congregate.helpers import conf, api, misc_utils
    from congregate.helpers import logger as log
    from congregate.migration import users, groups
    from congregate.aws.presigned import generate_presigned_url
    from congregate.aws.import_from_s3 import import_from_s3
    from congregate.cli.stage_projects import stage_projects

conf = conf.ig()

l = log.congregate_logger(__name__)

app_path = os.getenv("CONGREGATE_PATH")

parent_host = conf.parent_host
parent_token = conf.parent_token

def export_project(project):
    if isinstance(project, str):
        project = json.loads(project)
    name = "%s_%s.tar.gz" % (project["namespace"], project["name"])
    presigned_put_url = generate_presigned_url(name, "PUT")
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
    except urllib2.HTTPError, e:
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
    for member in project["members"]:
        if project["namespace"] == member["username"]:
            user_project = True
            #namespace = project["namespace"]
            new_user = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "users/%d" % member["id"]))
            namespace = new_user["username"]
            l.logger.info("%s is a user project belonging to %s. Attempting to import into their namespace" % (project["name"], new_user))
            break
    if not user_project:
        l.logger.info("%s is not a user project. Attempting to import into a group namespace" % (project["name"]))
        if conf.parent_id is not None:
            response = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "groups/%d" % conf.parent_id))
            namespace = "%s/%s" % (response["path"], project["namespace"])
        else:
            namespace = project["namespace"]
    presigned_get_url = generate_presigned_url(filename, "GET")
    exported = False
    import_response = None
    timeout = 0
    while not exported:
        import_response = import_from_s3(name, namespace, presigned_get_url, filename)
        #print import_response
        import_id = None
        if import_response is not None and len(import_response) > 0:
            l.logger.info(import_response)
            import_response = json.loads(import_response)
            if import_response.get("id") is not None:
                import_id = import_response["id"]
            elif import_response.get("message") is not None:
                if "Name has already been taken" in import_response.get("message"):
                    l.logger.debug("Searching for %s" % project["name"])
                    search_response = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "projects?search=%s" % project["name"]))
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
                status = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "projects/%d/import" % import_id))
                l.logger.info(status)
                if status["import_status"] == "finished":
                    l.logger.info("%s has been exported and import is occurring" % name)
                    exported = True
                    if conf.mirror_username is not None:
                        mirror_repo(project, import_id)
                elif status["import_status"] == "failed":
                    l.logger.info("%s failed to import" % name)
                    exported = True
        else:
            if timeout < 60:
                l.logger.info("Waiting on %s to upload" % name)
                timeout += 1
                time.sleep(1)
            else:
                l.logger.info("Moving on to the next project. Time limit exceeded")
                break
    
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
        new_project = json.load(api.generate_get_request(parent_host, parent_token, "projects?search=%s" % project["name"]))
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
                    except urllib2.HTTPError, e:
                        l.logger.error(e)
                        l.logger.error("Member might already exist. Attempting to update access level")
                        try:
                            api.generate_put_request(parent_host, parent_token, "projects/%d/members/%d?access_level=%d" % (new_project[0]["id"], member["id"], member["access_level"]), data=None)
                        except urllib2.HTTPError, e:
                            l.logger.error(e)
                            l.logger.error("Attempting to update existing member failed")

                if not root_user_present:
                    l.logger.info("removing root user from project")
                    api.generate_delete_request(parent_host, parent_token, "projects/%d/members/%d" % (new_project[0]["id"], conf.parent_user_id))

def migrate_single_project_info(project):
    """
        Subsequent function to update project info AFTER import
    """
    members = project["members"]
    project.pop("members")
    l.logger.info("Searching for %s" % project["name"])
    new_project = json.load(api.generate_get_request(parent_host, parent_token, "projects?search=%s" % project["name"]))
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
                except urllib2.HTTPError, e:
                    l.logger.error(e)
                    l.logger.error("Member might already exist. Attempting to update access level")
                    try:
                        api.generate_put_request(parent_host, parent_token, "projects/%d/members/%d?access_level=%d" % (new_project[0]["id"], member["id"], member["access_level"]), data=None)
                    except urllib2.HTTPError, e:
                        l.logger.error(e)
                        l.logger.error("Attempting to update existing member failed")

            # if not root_user_present:
            #     l.logger.info("removing root user from project")
            #     api.generate_delete_request(parent_host, parent_token, "projects/%d/members/%d" % (new_project[0]["id"], conf.parent_user_id))


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
        response_json = json.loads(response.read())
        if len(response_json) > 0:
            l.logger.debug(len(response_json))
            # for i in range(len(response_json)):
            #     appended_data = response_json[i]
            #     appended_data["environment_scope"] = "*"
            #     wrapped_data = json.dumps(appended_data)
            #     api.generate_post_request(conf.parent_host, conf.parent_token, "projects/%d/variables" % import_id, wrapped_data)
        else:
            l.logger.info("Project does not have CI variables. Skipping.")

    except urllib2.HTTPError, e:
        l.logger.error(e)
        return None

def migrate_projects(project_json):
    if isinstance(project_json, str):
        project_json = json.loads(project_json)
    l.logger.debug("Searching for existing %s" % project_json["name"])
    project_exists = False
    search_response = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "projects?search=%s" % project_json["name"]))
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
            response = json.load(api.generate_get_request(conf.child_host, conf.child_token, "projects/%d/export" % project_json["id"]))
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
        if exported:
            #import_id = import_project(project_json)
            #if import_id is not None:
            #    migrate_variables(import_id, project_json["id"])
            #    migrate_single_project_info(project_json)
            migrate_given_export(project_json)

def migrate_given_export(project_json):
    if isinstance(project_json, str):
        project_json = json.loads(project_json)
    l.logger.debug("Searching for existing %s" % project_json["name"])
    project_exists = False
    project_id = None
    try:
        search_response = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "projects?search=%s" % project_json["name"]))
        if len(search_response) > 0:
            for proj in search_response:
                if proj["name"] == project_json["name"] and project_json["namespace"] in proj["namespace"]["path"]:
                    l.logger.info("Project already exists. Skipping %s" % project_json["name"])
                    project_exists = True
                    project_id = proj["id"]
                    break
        if project_id:
            import_check = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "projects/%d/import" % project_id))
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
            if import_id is not None:
                migrate_variables(import_id, project_json["id"])
                migrate_single_project_info(project_json)
    except urllib2.HTTPError, e:
        l.logger.error(e)
    except OverflowError, e:
        l.logger.error(e)
    except requests.ConnectionError, e:
        l.logger.error(e)
        
def migrate():
    with open("%s/data/stage.json" % app_path, "r") as f:
        files = json.load(f)
    with open("%s/data/staged_groups.json" % app_path, "r") as f:
        groups_file = json.load(f)

    l.logger.info("Migrating user info")
    new_users = users.migrate_user_info()

    # with open("%s/data/new_user_ids.txt" % app_path, "w") as f:
    #     for new_user in new_users:
    #         f.write("%s\n" % new_user)

    # if len(new_users) > 0:
    #     users.update_user_info(new_users)
    # else:
    #     users.update_user_info(new_users, overwrite=False)
    
    if len(groups_file) > 0:
        l.logger.info("Migrating group info")
        groups.migrate_group_info()
    else:
        l.logger.info("No groups to migrate")

    if len(files) > 0:
        l.logger.info("Migrating project info")
        # add some multithreading?
        pool = ThreadPool(2) 
        # Open the urls in their own threads
        # and return the results
        results = pool.map(handle_migrating_file, files)
        #close the pool and wait for the work to finish 
        pool.close() 
        pool.join() 

        #migrate_project_info()
    else:
        l.logger.info("No projects to migrate")

def kick_off_import():
    with open("%s/data/stage.json" % app_path, "r") as f:
        files = json.load(f)
    if len(files) > 0:
        l.logger.info("Importing projects")
        # add some multithreading?
        pool = ThreadPool(4) 
        # Open the urls in their own threads
        # and return the results
        results = pool.map(migrate_given_export, files)
        #close the pool and wait for the work to finish 
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
            parent_namespace = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "groups/%d" % conf.parent_id))
            namespace = "%s/%s" % (parent_namespace["path"], f["namespace"])
        else:
            namespace = f["namespace"]
        if conf.location == "filesystem":
            l.logger.info("Exporting %s to %s" % (name, conf.filesystem_path))
            api.generate_post_request(conf.child_host, conf.child_token, "projects/%d/export" % id, "")
            if working_dir != conf.filesystem_path:
                os.chdir(conf.filesystem_path)
            download = api.generate_get_request(conf.child_host, conf.child_token, "projects/%d/export/download" % id)
            filename = download.info().getheader("Content-Disposition").split("=")[1]
            with open("%s/downloads/%s" % (conf.filesystem_path, filename), "w") as f:
                f.write(download)
            
            data = {
                "path": name,
                "file": "%s/downloads/%s" % (conf.filesystem_path, filename),
                "namespace": namespace
            }

            api.generate_post_request(conf.parent_host, conf.parent_token, "projects/import", urllib.urlencode(data))

            #migrate_project_info()

        elif (conf.location).lower() == "aws":
            l.logger.info("Exporting %s to S3" % name)
            migrate_projects(f)
    except IOError, e:
        l.logger.error(e)

def find_unimported_projects():
    unimported_projects = []
    with open("%s/data/stage.json" % app_path, "r") as f:
        files = json.load(f)
    if len(files) > 0:
        for project_json in files:
            try:
                l.logger.debug("Searching for existing %s" % project_json["name"])
                project_exists = False
                search_response = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "projects?search=%s" % (project_json["name"])))
                if len(search_response) > 0:
                    for proj in search_response:
                        if proj["name"] == project_json["name"]:
                            if "%s" % project_json["namespace"].lower() in proj["path_with_namespace"].lower():
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
                search_response = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "projects?search=%s" % (project_json["name"])))
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
                search_response = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "projects?search=%s" % (project_json["name"])))
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
        project = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "projects/%d" % i))
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
        #print group
        if group.get("child_ids", None) is not None:
            for child_id in group["child_ids"]:
                sub_count += api.get_count(conf.parent_host, conf.parent_token, "groups/%d/projects" % child_id)
        #print "%s has %d projects" % (group["name"], count)
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
