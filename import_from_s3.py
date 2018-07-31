"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import requests
import urllib
import json
import sys
import os

name = sys.argv[1]
namespace = sys.argv[2]
presigned_url = sys.argv[3]

filename = "%s.tar.gz" % name

app_path = os.getenv("CONGREGATE_PATH")

# Loading project config
with open('%s/data/config.json' % app_path) as f:
    data = json.load(f)["config"]

api_url = data["parent_instance_host"]
api_token = data["parent_instance_token"]

s3_file = urllib.urlopen(presigned_url)

url =  '%s/api/v4/projects/import' % (api_url)
files = {'file': s3_file}
data = {
    "path": name,
    "namespace": namespace
}
headers = {
    'Private-Token': api_token
}

r = requests.post(url, headers=headers, data=data, files=files)

# Returning response
print r.text
