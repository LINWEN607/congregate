"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import sys
import json

with open("data/stage.json", "r") as f:
    staged_projects = json.load(f)

with open("data/new_user.json", "r") as f:
    new_users = json.load(f)

for i in range(len(staged_projects)):
    for member in staged_projects[i]["members"]:
        for new_user in new_users:
            if member["username"] == new_user["username"]:
                member["id"] = new_user["id"]
    
with open("data/stage.json", "w") as f:
    json.dumps(staged_projects, f)