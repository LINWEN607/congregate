import json
import http.client
import os
import sys

from urllib.parse import quote_plus

def traverse_dir(directory):
    files = []
    for root, dir, filenames in os.walk(directory):
        for fn in filenames:
            if root != directory:
                files.append(f"{''.join(root.split('/')[1:])}/{fn}")
            else:
                files.append(fn)
    return files

PID = sys.argv[1]
EXTRAS = sys.argv[2] if len(sys.argv) > 2 else None
T1 = os.getenv("MIGRATION_TEMPLATE_TOKEN")
T2 = os.getenv("PS_MIGRATION_TOKEN")

rpath = 'runbooks'
conn = http.client.HTTPSConnection("gitlab.com")
arr = [x for x in traverse_dir(rpath) if x != "README.md"]
arr2 = [x for x in os.listdir(
    ".") if "migration-features-matrix.md" in x or x == "famq.md"] if EXTRAS else []
arr = arr + arr2
arr_length = len(arr)
for i, x in enumerate(arr):
    with open(x if x in arr2 else os.path.join(rpath, x), 'r') as f:
        # Files going to the migration-template root folder
        if x in arr2 and EXTRAS:
            file_path = quote_plus(x)
        else:
            runbook_path = f".gitlab/issue_templates/{x}"
            file_path = quote_plus(runbook_path)

        data = {
            "file_path": file_path,
            "branch": "master",
            "content": str(f.read())
        }

        if i != (arr_length - 1):
            data["commit_message"] = "Uploading docs [skip-ci]"
        else:
            data["commit_message"] = "Uploading docs files"

        url = f"/api/v4/projects/{PID}/repository/files/{file_path}"
        payload = json.dumps(data)
        headers = {
            'Private-Token': T1 if EXTRAS else T2,
            'Content-Type': "application/json"
        }

        print(f"Uploading file {x} to project {PID} file path {file_path}")
        conn.request("POST", url, payload, headers)

        res = conn.getresponse()
        data = res.read()
        print(f"{res.status} - {data.decode('utf-8')}")
        if res.status == 400:
            print(f"Updating project {PID} file {file_path} based on changes in {x}")
            conn.request("PUT", url, payload, headers)
            res1 = conn.getresponse()
            data1 = res1.read()
            print(f"{res1.status} - {data1.decode('utf-8')}")
