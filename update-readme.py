import congregate
import re
import json
import os
import requests
from collections import OrderedDict

private_token = os.getenv('ACCESS_TOKEN')
gitlab_user_email = os.getenv('GITLAB_USER_EMAIL')
gitlab_user_name = os.getenv('GITLAB_USER_NAME')
project_id = os.getenv('CI_PROJECT_ID')

docs = congregate.__doc__.split("\n")
cleaned_docs = "\n".join(docs[4:])

def traverse_file(base_obj, level, string=None):
    header_level = ""
    for x in range(level):
        header_level += "#"
    pattern_string = "^%s .+\n" % header_level
    pattern = re.compile(pattern_string)
    if string is not None:
        raw_string = string
    else:
        raw_string = base_obj["raw"]
    if len(pattern.findall(raw_string)) == 0:
        pattern_string = "\n%s .+\n" % header_level
        pattern = re.compile(pattern_string)

    split_string = re.split(pattern_string, raw_string)
    keys = pattern.findall(raw_string)
    for key in keys:
        base_obj[key] = OrderedDict({
            "raw": split_string[keys.index(key)+1]
        })
        traverse_file(base_obj[key], level+1)

def traverse_obj(obj):
    final = ""
    for k,v in obj.items():
        if k != "raw":
            final += k
        if "Usage" in k:
            obj[k]["raw"]
            obj[k]["raw"] = "```\n%s```\n" % cleaned_docs
        if "\n## " in v:
            split = v.split("\n\n## ")[0]
            final += split
            final += "\n"
        elif "\n### " in v:
            pass
        elif isinstance(v, dict):
            final += traverse_obj(OrderedDict(v))
        else:
            final += v
    return final


deconstructed_readme = OrderedDict()
transient_obj = OrderedDict()

with open("README.md", 'r') as f:
    readme = f.read()

traverse_file(deconstructed_readme, 1, string=readme)
updated_md = traverse_obj(deconstructed_readme)

headers = {
    "Private-Token": private_token
}

data = {
    "branch": "master", 
    "author_email": gitlab_user_email, 
    'author_name': gitlab_user_name, 
    'commit_message': 'Updating usage info',
    "content": updated_md
}

r = requests.put('https://gitlab.com/api/v4/projects/%s/repository/files/README.md' % project_id, data=data, headers=headers)

print r.text