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
try:
    from helpers import conf, api, misc_utils
    from migration import users, groups
    from aws.presigned import generate_presigned_url
    from aws.import_from_s3 import import_from_s3
except ImportError:
    from congregate.helpers import conf, api, misc_utils
    from congregate.migration import users, groups
    from congregate.aws.presigned import generate_presigned_url
    from congregate.aws.import_from_s3 import import_from_s3



conf = conf.ig()

app_path = os.getenv("CONGREGATE_PATH")

parent_host = conf.parent_host
parent_token = conf.parent_token

def export_project(project):
    if isinstance(project, str):
        project = json.loads(project)
    name = project["name"] + ".tar.gz"
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
    if isinstance(project, str):
        project = json.loads(project)
    name = project["name"]
    if conf.parent_id is not None:
        response = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "groups/%d" % conf.parent_id))
        namespace = "%s/%s" % (response["path"], project["namespace"])
    else:
        namespace = project["namespace"]
    presigned_get_url = generate_presigned_url(name + ".tar.gz", "GET")
    exported = False
    import_response = None

    while not exported:
        import_response = import_from_s3(name, namespace, presigned_get_url)
        if import_response is not None:
            if "\"message\":" in import_response:
                print import_response
                break
            print import_response
            import_id = json.loads(import_response)["id"]
            status = api.generate_get_request(conf.parent_host, conf.parent_token, "projects/%d/import" % import_id)
            if isinstance(status, str):
                status = json.load(status)
            else:
                status = json.loads(status.read())
            if status["import_status"] == "finished":
                print "%s has been exported and import is occurring" % name
                exported = True
            else:
                print "Waiting on %s to export" % name
                time.sleep(0.5)
        else:
            print "Waiting on %s to export" % name
            time.sleep(0.5)
    
    return import_response

def migrate_project_info():
    with open("%s/data/stage.json" % app_path, "r") as f:
        projects = json.load(f)
    
    for project in projects:
        members = project["members"]
        project.pop("members")
        new_project = json.load(api.generate_get_request(parent_host, parent_token, "projects?search=%s" % project["name"]))
        if len(new_project) > 0:
            if new_project[0]["name"] == project["name"]:
                root_user_present = False
                for member in members:
                    if member["id"] == 1:
                        root_user_present = True
                    new_member = {
                        "user_id": member["id"],
                        "access_level": member["access_level"]
                    }

                    try:
                        api.generate_post_request(parent_host, parent_token, "projects/%d/members" % new_project[0]["id"], json.dumps(new_member))
                    except urllib2.HTTPError, e:
                        print e

                if not root_user_present:
                    print "removing root user from project"
                    api.generate_delete_request(parent_host, parent_token, "projects/%d/members/1" % new_project[0]["id"])

def migrate_variables(import_response, id):
    response = api.generate_get_request(conf.child_host, conf.child_token, "projects/%d/variables" % id)
    response_json = json.loads(response.read())

    for i in range(len(response_json)):
        appended_data = response_json[i]
        appended_data["environment_scope"] = "*"
        wrapped_data = urllib.urlencode(appended_data)
        api.generate_post_request(conf.parent_host, conf.parent_token, "projects/%d/variables" % import_response["id"], wrapped_data)

def migrate_projects(project_json):
    if isinstance(project_json, str):
        project_json = json.loads(project_json)
    export_project(project_json)
    import_json = import_project(project_json)
    print project_json
    print import_json
    if import_json is not None:
        migrate_variables(import_json, project_json["id"])
        migrate_project_info()

def migrate():
    with open("%s/data/stage.json" % app_path, "r") as f:
        files = json.load(f)
    
    users.migrate_user_info()
    users.update_user_info()
    groups.migrate_group_info()

    working_dir = os.getcwd()

    for f in files:
        name = f["name"]
        id = f["id"]
        if conf.parent_id is not None:
            parent_namespace = json.load(api.generate_get_request(conf.parent_host, conf.parent_token, "groups/%d" % conf.parent_id))
            namespace = "%s/%s" % (parent_namespace["path"], f["namespace"])
        else:
            namespace = f["namespace"]
        if conf.location == "filesystem":
            print "Exporting %s to %s" % (name, conf.filesystem_path)
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

            migrate_project_info()

        elif (conf.location).lower() == "aws":
            print "Exporting %s to S3" % name
            migrate_projects(f)

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