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
from helpers.api import *
from helpers.conf import ig
from aws.presigned import generate_presigned_url
from aws.import_from_s3 import import_from_s3

conf = ig()

app_path = os.getenv("CONGREGATE_PATH")

parent_host = conf.parent_host
parent_token = conf.parent_token

def export_project(project):
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
        generate_post_request(conf.child_host, conf.child_token, "projects/%d/export" % project["id"], "&".join(upload), headers=headers)
    except urllib2.HTTPError, e:
       pass

def import_project(project):
    project_json = json.loads(project)
    name = project_json["name"]
    namespace = project_json["namespace"]
    presigned_get_url = generate_presigned_url(name + ".tar.gz", "GET")
    exported = False
    import_response = None

    while not exported:
        import_response = import_from_s3(name, namespace, presigned_get_url)
        if import_response is not None:
            print "%s has been exported and import is occurring" % name
            exported = True
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
        new_project = json.load(generate_get_request(parent_host, parent_token, "projects?search=%s" % project["name"]))
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
                        generate_post_request(parent_host, parent_token, "projects/%d/members" % new_project[0]["id"], json.dumps(new_member))
                    except urllib2.HTTPError, e:
                        print e

                if not root_user_present:
                    print "removing root user from project"
                    generate_delete_request(parent_host, parent_token, "projects/%d/members/1" % new_project[0]["id"])

def migrate_variables(import_response, id):
    response = generate_get_request(conf.child_host, conf.child_token, "projects/%d/variables" % id)
    response_json = json.loads(response.read())

    for i in range(len(response_json)):
        appended_data = response_json[i]
        appended_data["environment_scope"] = "*"
        wrapped_data = urllib.urlencode(appended_data)
        generate_post_request(conf.parent_host, conf.parent_token, "projects/%d/variables" % import_response["id"], wrapped_data)

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
        export_project(project_json)
        import_json = import_project(project_json)
        migrate_variables(import_json, json.loads(project_json)["id"])
        migrate_project_info()