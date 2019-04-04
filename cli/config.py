import os
import subprocess
import json
import time
try:
    from helpers.api import generate_get_request
except ImportError:
    from congregate.helpers.api import generate_get_request

app_path = os.getenv("CONGREGATE_PATH")

def generate_config():
    config = {}
    wrapper = {}

    print "##Configuring congregate"

    external = raw_input("%s. Migration source (default: GitLab) " % str(len(config) + 1))
    if len(external) > 0 and external.lower() != "gitlab":
        config["external_source"] = external
        print "External migration is currently limited to mirroring through http/https. A master username and password will be required to set up mirroring in each shell project."
        external_username = raw_input("%s. External username: " % str(len(config) + 1))
        config["external_user_name"] = external_username
        external_password = raw_input("%s. External password: " % str(len(config) + 1))
        config["external_user_password"] = external_password
        list_of_repos = raw_input("%s. Path to JSON file containing repo information: " % str(len(config) + 1))
        if len(list_of_repos) > 0:
            if list_of_repos[0] != "/":
                config["repo_list_path"] = "%s/%s" % (app_path, list_of_repos)
            else:
                config["repo_list_path"] = list_of_repos
    else:
        config["external_source"] = False

    parent_instance_host = raw_input("%s. Host of parent instance (destination instance) " % str(len(config) + 1))
    config["parent_instance_host"] = parent_instance_host

    parent_instance_token = raw_input("%s. Access token to use for parent instance " % str(len(config) + 1))
    config["parent_instance_token"] = parent_instance_token

    parent_user_info = get_user(parent_instance_host, parent_instance_token)

    config["parent_user_id"] = parent_user_info["id"]

    if config["external_source"] == False:
        child_instance_host = raw_input("%s. Host of child instance (source instance) " % str(len(config) + 1))
        config["child_instance_host"] = child_instance_host

        child_instance_token = raw_input("%s. Access token to use for child instance " % str(len(config) + 1))
        config["child_instance_token"] = child_instance_token

        parent_id = raw_input("Are you migrating the entire instance to a group? For example, migrating to our SaaS solution? (default: no)")
        if parent_id != "no" and len(parent_id) > 0:
            parent_id = raw_input("%s. Please input the parent group ID (You can find this in the parent group -> settings -> general)" % str(len(config) + 1))
            config["parent_id"] = int(parent_id)

        mirror_user = raw_input("Are you planning a soft cut-over migration? (Mirroring repos to keep both instances around) (default: no)")
        if mirror_user != "no" and len(mirror_user) > 0:
            mirror_user = parent_user_info["username"]
            config["mirror_username"] = mirror_user

        location = raw_input("%s. Staging location type for exported projects [filesystem, filesystem-aws, aws]? (default: filesystem) " % str(len(config) + 1))
        if len(location) == 0 or location == "filesystem":
            config["location"] = "filesystem"
            location = "filesystem"
        else:
            config["location"] = location

        if "filesystem" in location.lower():
            path = raw_input("%s. Absolute path for exported projects? (default: %s) " % (str(len(config) + 1), os.getcwd()))
            if len(path) > 0 and path != os.getcwd():
                config["path"] = path
            else:
                config["path"] = os.getcwd()

        if "aws" in location.lower():
            bucket_name = raw_input("%s. Bucket name: " % str(len(config) + 1))
            config["bucket_name"] = bucket_name
            access_key = raw_input("%s. Access key for S3 bucket: " % str(len(config) + 1))
            config["access_key"] = access_key
            command = "aws configure set aws_access_key_id %s" % access_key
            subprocess.call(command.split(" "))
            secret_key = raw_input("%s. Secret key for S3 bucket: " % str(len(config) + 1))
            config["secret_key"] = secret_key
            command = "aws configure set aws_secret_access_key %s" % secret_key
            subprocess.call(command.split(" "))

    config["number_of_threads"] = 2

    wrapper["config"] = config
    return wrapper


def config():
    config = generate_config()
    with open("%s/data/config.json" % app_path, "w") as f:
        f.write(json.dumps(config, indent=4))
    time.sleep(1)
    print "Congregate has been successfully configured"

def update_config(config_data):
    with open("%s/data/config.json" % app_path, "r") as f:
        data = json.load(f)
    data["config"] = json.loads(config_data)
    with open("%s/data/config.json" % app_path, "w") as f:
        json.dump(data, f, indent=4)

def get_user(parent_instance_host, parent_instance_token):
    return generate_get_request(parent_instance_host, parent_instance_token, "user").json()
