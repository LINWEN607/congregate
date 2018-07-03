import requests
import urllib
import json
import sys

name = sys.argv[1]
namespace = sys.argv[2]
presigned_url = sys.argv[3]

filename = "%s.tar.gz" % name

with open('config.json') as f:
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
print r.text
