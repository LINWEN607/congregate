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

if __name__ == "__main__":
    if (not os.path.isfile('%s/data/project_json.json' % app_path)):
        #TODO: rewrite this logic to handle subprocess more efficiently
        cmd = "%s/list_projects.sh > /dev/null" % app_path
        subprocess.call(cmd.split())

    # Loading project config
    with open('%s/data/config.json' % app_path) as f:
        config = json.load(f)["config"]

    # Loading projects information
    with open('%s/data/project_json.json' % app_path) as f:
        projects = json.load(f)

    # Rewriting projects to retrieve objects by ID more efficiently
    rewritten_projects = {}
    for i in range(len(projects)):
        new_obj = projects[i]
        id_num = projects[i]["id"]
        rewritten_projects[id_num] = new_obj

    if sys.argv[1] == "all" or sys.argv[1] == ".":
        for i in range(len(projects)):
            obj = {}
            obj["id"] = projects[i]["id"]
            obj["name"] = projects[i]["name"]
            obj["namespace"] = projects[i]["path_with_namespace"].split("/")[0]
            obj["path_with_namespace"] = projects[i]["path_with_namespace"]
            obj["visibilty"] = projects[i]["visibility"]
            response = generate_response(config["child_instance_host"], config["child_instance_token"], projects[i]["id"], None, "projects")
            obj["members"] = json.loads(response.read())
            staging.append(obj)
    else:
        for i in range(1, len(sys.argv)):
            obj = {}
            # Hacky check for id or project name by explicitly checking variable type
            try:
                if (isinstance(int(sys.argv[i]), int)):
                    key = sys.argv[i]
                    # Retrieve object from better formatted object
                    project = rewritten_projects[int(key)]
            except ValueError:
                # Iterate over original project_json.json file
                for j in range(len(projects)):
                    if projects[j]["name"] == sys.argv[i]:
                        project = projects[j]

            obj["id"] = project["id"]
            obj["name"] = project["name"]
            obj["namespace"] = project["path_with_namespace"]
            obj["visibilty"] = project["visibility"]
            response = generate_response(config["child_instance_host"], config["child_instance_token"], project["id"], None, "projects")
            obj["members"] = json.loads(response.read())
            staging.append(obj)

    if (len(staging) > 0):
        with open("%s/data/stage.json" % app_path, "wb") as f:
            f.write(json.dumps(staging, indent=4))

