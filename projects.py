"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import json
import sys
import subprocess
import argparse
import urllib2
from helpers import api

app_path = os.getenv("CONGREGATE_PATH")

with open('%s/data/config.json' % app_path) as f:
    config = json.load(f)["config"]

child_host = config["child_instance_host"]
child_token = config["child_instance_token"]
parent_host = config["parent_instance_host"]
parent_token = config["parent_instance_token"]

def migrate_project_info():
    with open("%s/data/stage.json" % app_path, "r") as f:
        projects = json.load(f)
    
    for project in projects:
        members = project["members"]
        project.pop("members")
        new_project = json.load(api.generate_get_request(parent_host, parent_token, "projects?search=%s" % project["name"]))

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle project-related tasks')
    parser.add_argument('--retrieve', type=bool, default=False, dest='retrieve',
                    help='Retrieve project info and save it to %s/data/projects.json' % app_path)
    parser.add_argument('--migrate', type=bool, default=False, dest='migrate',
                    help='Migrate all project info to parent instance')
    parser.add_argument('--quiet', type=bool, default=False, dest='quiet',
                    help='Silent output of script')

    args = parser.parse_args()

    retrieve = args.retrieve
    migrate = args.migrate
    quiet = args.quiet

    if retrieve:
        #retrieve_project_info()
        pass
    
    if migrate:
        migrate_project_info()