import json
import os
from helpers import conf
from helpers import api
from migration import groups, users

app_path = os.getenv("CONGREGATE_PATH")

def list_projects():
    config = conf.ig()

    print "Listing projects from %s" % config.child_host

    projects = json.load(api.generate_get_request(config.child_host, config.child_token, "projects?page=1&per_page=100"))

    with open("%s/data/project_json.json" % app_path, "wb") as f:
        json.dump(projects, f, indent=4)

    for project in projects:
        id = project["id"]
        name = project["name"]
        description = project["description"]
        print "[id: %s] %s: %s" % (id, name, description)

    groups.retrieve_group_info(quiet=True)
    users.retrieve_user_info(quiet=True)

if __name__ == "__main__":
    list_projects()