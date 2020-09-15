import json
import http.client
import os
import sys

project_id = sys.argv[-1]

files = os.listdir('runbooks')
path = 'runbooks/'
conn = http.client.HTTPSConnection("gitlab.com")
arr = [x for x in os.listdir("runbooks") if x != "README.md"]
arr_length = len(arr)
for i, x in enumerate(arr):
    xpath = os.path.join(path,x)
    with open(xpath, 'r') as f:
        l = f.read()
        if i != (arr_length - 1):
            data = {"branch": "master", "author_email": "sfirdaus@gitlab.com", "author_name": "Syeda Firdaus", "commit_message": "Uploading runbook files [skip-ci]", "content": str(l)}
        else:
            data = {"branch": "master", "author_email": "sfirdaus@gitlab.com", "author_name": "Syeda Firdaus", "commit_message": "Uploading runbook files", "content": str(l)}
            payload = json.dumps(data)
            headers = {
                'private-token': os.getenv("PS_MIGRATION_TOKEN"),
                'content-type': "application/json"
            }
            url = f"/api/v4/projects/{project_id}/repository/files/.gitlab%2Fissue_templates%2F"+x+""
            conn.request("POST", url, payload, headers)

        res = conn.getresponse()
        data = res.read()
        print(res.status)
        print(data.decode("utf-8"))
        if res.status == 400:
            conn.request("PUT", url, payload, headers)
            res1 = conn.getresponse()
            data1 = res1.read()
            print(res1.status)
            print(data1.decode("utf-8"))
