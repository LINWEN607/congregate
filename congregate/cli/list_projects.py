import json
import os
from congregate.helpers import api
from congregate.helpers import base_module as b
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.projects import ProjectsClient

groupsclient = GroupsClient()
usersclient = UsersClient()
projectsclient = ProjectsClient()


def list_projects():

    print "Listing projects from %s" % b.config.child_host

    projects = list(api.list_all(b.config.child_host,
                                 b.config.child_token, "projects"))

    with open("%s/data/project_json.json" % b.app_path, "wb") as f:
        json.dump(projects, f, indent=4)

    for project in projects:
        id = project["id"]
        name = project["name"]
        description = project["description"]
        print "[id: %s] %s: %s" % (id, name, description)

    groupsclient.retrieve_group_info(b.config.child_host, b.config.child_token, quiet=True)
    usersclient.retrieve_user_info(quiet=True)

    staged_files = ["stage", "staged_groups", "staged_users"]

    for filename in staged_files:
        write_empty_file(filename)


def write_empty_file(filename):
    if not os.path.isfile("%s/data/%s.json" % (b.app_path, filename)):
        with open("%s/data/%s.json" % (b.app_path, filename), "w") as f:
            f.write("[]")


if __name__ == "__main__":
    list_projects()
