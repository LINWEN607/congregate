import api
import json
import sys
from helpers import conf

''' 
Usage

cd this directory

python cli.py <cmd>

examples:
python cli.py enable_mirroring
python cli.py set_default_branch
python cli.py update_diverging_branch

'''

def enable_mirroring():
    for project in api.list_all(config.parent_host, config.parent_token, "projects"):
        if isinstance(project, dict):
            encoded_name = project["name"].encode('ascii','replace')
            if project.get("import_status", None) == "failed":
                print "Enabling mirroring for %s" % encoded_name
                try:
                    resp = api.generate_post_request(config.parent_host, config.parent_token, "projects/%d/mirror/pull" % project["id"], None)
                    print "Status: %d" % resp.status_code
                except Exception, e:
                    print e
                    print "Skipping %s" % encoded_name
            else:
                if project.get("name", None) is not None:
                    print "Skipping %s" % encoded_name
        else:
            print "Skipping %s" % project

def set_default_branch():
    for project in api.list_all(config.parent_host, config.parent_token, "projects"):
        if project.get("default_branch", None) != "master":
            id = project["id"]
            name = project["name"]
            print "Setting default branch to master for project %s" % name
            resp = api.generate_put_request(config.parent_host, config.parent_token, "projects/%d?default_branch=master" % id, data=None)
            print "Status: %d" % resp.status_code

def update_diverging_branch():
    for project in api.list_all(config.parent_host, config.parent_token, "projects"):
        if project.get("mirror_overwrites_diverged_branches", None) != True:
            id = project["id"]
            name = project["name"]
            print "Setting mirror_overwrites_diverged_branches to true for project %s" % name
            resp = api.generate_put_request(config.parent_host, config.parent_token, "projects/%d?mirror_overwrites_diverged_branches=true" % id, data=None)
            print "Status: %d" % resp.status_code

def archive_instance():
    for project in api.list_all(config.parent_host, config.parent_token, "projects"):
        if isinstance(project, dict):
            encoded_name = project["name"].encode('ascii','replace')
            print "Archiving %s" % encoded_name
            try:
                resp = api.generate_put_request(config.parent_host, config.parent_token, "projects/%d?archived=true" % project["id"], None)
                print "Status: %d" % resp.status_code
            except Exception, e:
                print e
                print "Archiving failed. Skipping %s" % encoded_name
        else:
            if project.get("name", None) is not None:
                print "Skipping %s" % encoded_name


if __name__ == "__main__":
    config = conf.ig()
    cmd = sys.argv[1]
    if cmd == "enable_mirroring":
        enable_mirroring()
    elif cmd == "set_default_branch":
        set_default_branch()
    elif cmd == "update_diverging_branch":
        update_diverging_branch()
    elif cmd == "archive_instance":
        archive_instance()
