import json
import os
from helpers import conf
from helpers import api
from helpers import logger as log
from migration import groups, users

app_path = os.getenv("CONGREGATE_PATH")
config = conf.ig()
l = log.congregate_logger(__name__)

def list_projects():

    print "Listing projects from %s" % config.child_host

    projects = list(api.list_all(config.child_host, config.child_token, "projects"))

    with open("%s/data/project_json.json" % app_path, "wb") as f:
        json.dump(projects, f, indent=4)

    for project in projects:
        id = project["id"]
        name = project["name"]
        description = project["description"]
        print "[id: %s] %s: %s" % (id, name, description)

    groups.retrieve_group_info(quiet=True)
    users.retrieve_user_info(quiet=True)

    staged_files = ["stage", "staged_groups", "staged_users"]

    for filename in staged_files:
        write_empty_file(filename)

def write_empty_file(filename):
    if not os.path.isfile("%s/data/%s.json" % (app_path, filename)):
        with open("%s/data/%s.json" % (app_path, filename), "w") as f:
            f.write("[]")

if __name__ == "__main__":
    list_projects()
