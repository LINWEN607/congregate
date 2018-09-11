"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import urllib
import urllib2
import json
import sys
import subprocess
from helpers import conf
from helpers import api



app_path = os.getenv("CONGREGATE_PATH")
staging = []

def generate_response(host, token, id, data, api):
    url = "%s/api/v4/%s/%d/members" % (host, api, int(id))
    headers = {
        'Private-Token': token
    }
    req = urllib2.Request(url, headers=headers, data=data)
    response = urllib2.urlopen(req)
    return response

def stage_projects(projects_to_stage):
    if (not os.path.isfile('%s/data/project_json.json' % app_path)):
        #TODO: rewrite this logic to handle subprocess more efficiently
        cmd = "%s/list_projects.sh > /dev/null" % app_path
        subprocess.call(cmd.split())

    config = conf.ig()

    # Loading projects information
    with open('%s/data/project_json.json' % app_path) as f:
        projects = json.load(f)

    # Rewriting projects to retrieve objects by ID more efficiently
    rewritten_projects = {}
    for i in range(len(projects)):
        new_obj = projects[i]
        id_num = projects[i]["id"]
        rewritten_projects[id_num] = new_obj

    if projects_to_stage[1] == "all" or projects_to_stage[1] == ".":
        for i in range(len(projects)):
            obj = {}
            obj["id"] = projects[i]["id"]
            obj["name"] = projects[i]["name"]
            obj["namespace"] = projects[i]["path_with_namespace"].split("/")[0]
            obj["path_with_namespace"] = projects[i]["path_with_namespace"]
            obj["visibilty"] = projects[i]["visibility"]
            response = generate_response(config.child_host, config.child_token, projects[i]["id"], None, "projects")
            obj["members"] = json.loads(response.read())
            staging.append(obj)
    else:
        for i in range(1, len(projects_to_stage)):
            obj = {}
            # Hacky check for id or project name by explicitly checking variable type
            try:
                if (isinstance(int(projects_to_stage[i]), int)):
                    key = projects_to_stage[i]
                    # Retrieve object from better formatted object
                    project = rewritten_projects[int(key)]
            except ValueError:
                # Iterate over original project_json.json file
                for j in range(len(projects)):
                    if projects[j]["name"] == projects_to_stage[i]:
                        project = projects[j]

            obj["id"] = project["id"]
            obj["name"] = project["name"]
            obj["namespace"] = project["path_with_namespace"]
            obj["visibilty"] = project["visibility"]
            response = generate_response(config.child_host, config.child_token, project["id"], None, "projects")
            obj["members"] = json.loads(response.read())
            staging.append(obj)

    if (len(staging) > 0):
        with open("%s/data/stage.json" % app_path, "wb") as f:
            f.write(json.dumps(staging, indent=4))

if __name__ == "__main__":
    stage_projects(sys.argv)

