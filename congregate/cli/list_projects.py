import json
import os
from congregate.helpers import api
from congregate.helpers import base_module as b
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.projects import ProjectsApi

groupsclient = GroupsClient()
usersclient = UsersClient()
projects_api = ProjectsApi()


def list_projects():

    print "Listing projects from %s" % b.config.source_host

    projects = list(projects_api.get_all_projects(b.config.source_host,
                                 b.config.source_token))

    with open("%s/data/project_json.json" % b.app_path, "wb") as f:
        json.dump(projects, f, indent=4)

    for project in projects:
        id = project["id"]
        name = project["name"]
        description = project["description"]
        print "[id: %s] %s: %s" % (id, name, description)

    groupsclient.retrieve_group_info(b.config.source_host, b.config.source_token, quiet=True)
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
