import os
import urllib
import urllib2
import json
import sys
import subprocess

app_path = os.getenv("CONGREGATE_PATH")
staging = []

def generate_response(host, token, id, data):
    url = "%s/api/v4//projects/%d/members" % (host, int(id))
    headers = {
        'Private-Token': token
    }
    req = urllib2.Request(url, headers=headers, data=data)
    response = urllib2.urlopen(req)
    return response

if __name__ == "__main__":
    if (not os.path.isfile('%s/data/project_json.json' % app_path)):
        cmd = "%s/list_projects.sh > /dev/null" % app_path
        subprocess.call(cmd.split())

    with open('%s/data/config.json' % app_path) as f:
        config = json.load(f)["config"]

    with open('%s/data/project_json.json' % app_path) as f:
        projects = json.load(f)

    rewritten_projects = {}
    for i in range(len(projects)):
        new_obj = projects[i]
        id_num = projects[i]["id"]
        rewritten_projects[id_num] = new_obj
        
    #print json.dumps(rewritten_projects, indent=4)

    if sys.argv[1] == "all" or sys.argv[1] == ".":
        for i in range(len(projects)):
            obj = {}
            obj["id"] = projects[i]["id"]
            obj["name"] = projects[i]["name"]
            obj["namespace"] = projects[i]["path_with_namespace"]
            obj["visibilty"] = projects[i]["visibility"]
            staging.append(obj)
    else:
        for i in range(1, len(sys.argv)):
            obj = {}
            try:
                if (isinstance(int(sys.argv[i]), int)):
                    key = sys.argv[i]
                    project = rewritten_projects[int(key)]
            except ValueError:
                for j in range(len(projects)):
                    if projects[j]["name"] == sys.argv[i]:
                        project = projects[j]

            obj["id"] = project["id"]
            obj["name"] = project["name"]
            obj["namespace"] = project["path_with_namespace"]
            obj["visibilty"] = project["visibility"]
            response = generate_response(config["child_instance_host"], config["child_instance_token"], project["id"], None)
            obj["members"] = json.loads(response.read())
            staging.append(obj)

    if (len(staging) > 0):
        with open("%s/data/stage.json" % app_path, "wb") as f:
            f.write(json.dumps(staging, indent=4))

            