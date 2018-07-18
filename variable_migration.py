"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import urllib
import urllib2
import json
import sys

app_path = os.getenv("CONGREGATE_PATH")

import_json = json.loads(sys.argv[1])

id = int(sys.argv[2])

with open('%s/data/config.json' % app_path) as f:
    config = json.load(f)["config"]

def generate_response(host, token, id, data):
    url = "%s/api/v4/projects/%d/variables" % (host, int(id))
    headers = {
        'Private-Token': token
    }
    req = urllib2.Request(url, headers=headers, data=data)
    response = urllib2.urlopen(req)
    return response

if __name__ == "__main__":
    response = generate_response(config["child_instance_host"], config["child_instance_token"], id, None)
    response_json = json.loads(response.read())

    for i in range(len(response_json)):
        appended_data = response_json[i]
        appended_data["environment_scope"] = "*"
        wrapped_data = urllib.urlencode(appended_data)
        generate_response(config["parent_instance_host"], config["parent_instance_token"], import_json["id"], wrapped_data)
