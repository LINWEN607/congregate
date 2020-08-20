import json
import http.client
import os

files = os.listdir('runbooks')
path = 'runbooks/'
arr = os.listdir(path)
conn = http.client.HTTPSConnection("gitlab.com")
for x in arr:
    if x != "README.md":
        xpath = os.path.join(path,x)
        with open(xpath, 'r') as f:
            l = f.read()
            data = {"branch": "runbooktest", "author_email": "sfirdaus@gitlab.com", "author_name": "Syeda Firdaus", "commit_message": "Uploading runbook files", "content": str(l)}
            payload = json.dumps(data)
            headers = {
                'private-token': os.getenv("PS_MIGRATION_TOKEN"),
                'content-type': "application/json"
            }
            url = "/api/v4/projects/11750578/repository/files/.gitlab%2Fissue_templates%2F"+x+""
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
