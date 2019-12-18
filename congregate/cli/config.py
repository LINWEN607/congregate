import os
import subprocess
import json
import time
from congregate.helpers.misc_utils import get_congregate_path
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi

app_path = get_congregate_path()
users = UsersApi()
groups = GroupsApi()

def generate_config():
    config = {}
    wrapper = {}

    print "## Configuring congregate"

    external = raw_input(
        "%s. Migration source (default: GitLab): " % str(len(config) + 1))
    if len(external) > 0 and external.lower() != "gitlab":
        config["external_source"] = external
        print("External migration is currently limited to mirroring through http/https. A master username and password will be required to set up mirroring in each shell project.")
        external_username = raw_input(
            "%s. External username: " % str(len(config) + 1))
        config["external_user_name"] = external_username
        external_password = raw_input(
            "%s. External password: " % str(len(config) + 1))
        config["external_user_password"] = external_password
        list_of_repos = raw_input(
            "%s. Path to JSON file containing repo information: " % str(len(config) + 1))
        if len(list_of_repos) > 0:
            if list_of_repos[0] != "/":
                config["repo_list_path"] = "%s/%s" % (app_path, list_of_repos)
            else:
                config["repo_list_path"] = list_of_repos
    else:
        config["external_source"] = False

    destination_instance_host = raw_input(
        "%s. Destination instance Host: " % str(len(config) + 1))
    config["destination_instance_host"] = destination_instance_host

    destination_instance_token = raw_input(
        "%s. Destination instance Access token: " % str(len(config) + 1))
    config["destination_instance_token"] = destination_instance_token

    destination_user_info = users.get_current_user(destination_instance_host, destination_instance_token)

    config["import_user_id"] = destination_user_info["id"]

    if config["external_source"] == False:
        source_instance_host = raw_input(
            "%s. Source instance Host: " % str(len(config) + 1))
        config["source_instance_host"] = source_instance_host

        source_instance_token = raw_input(
            "%s. Source instance Access token: " % str(len(config) + 1))
        config["source_instance_token"] = source_instance_token

        source_instance_registry = raw_input(
            "%s. Source instance Container Registry URL: " % str(len(config) + 1))
        config["source_instance_registry"] = source_instance_registry

        destination_instance_registry = raw_input(
            "%s. Destination instance Container Registry URL: " % str(len(config) + 1))
        config["destination_instance_registry"] = destination_instance_registry

        parent_id = raw_input(
            "Are you migrating the entire instance to a group? For example, migrating to our SaaS solution? (default: no) ")
        if parent_id != "no" and len(parent_id) > 0:
            parent_id = raw_input(
                "%s. Please input the parent group ID (You can find this in the parent group -> settings -> general) " % str(len(config) + 1))
            config["parent_id"] = int(parent_id)
            
            parent_group = groups.get_group(config["parent_id"], destination_instance_host, destination_instance_token).json()
            config["parent_group_path"] = parent_group["full_path"]
            print "Congregate is going to set all internal projects to private. You can change this setting later."
            config["make_visibility_private"] = True
            sso = raw_input("Are you migrating to a group with SAML SSO enabled? (default: no) ")
            if sso != "no" and len(sso) > 0:
                sso_provider = raw_input(
                    "%s. Please input the SSO provider (auth0, adfs, etc.) " % str(len(config) + 1))
                config["group_sso_provider"] = sso_provider
            username_suffix = raw_input(
                "In the case of username collisions, what suffix would you like to append to a username? (default: <leave empty>) ")
            if username_suffix != "_" and len(username_suffix) > 0:
                config["username_suffix"] = username_suffix

        mirror_user = raw_input(
            "Are you planning a soft cut-over migration? (Mirroring repos to keep both instances around) (default: no) ")
        if mirror_user != "no" and len(mirror_user) > 0:
            mirror_user = destination_user_info["username"]
            config["mirror_username"] = mirror_user

        location = raw_input(
            "%s. Staging location type for exported projects [filesystem, aws]? (default: filesystem) " % str(len(config) + 1))
        if len(location) == 0 or location == "filesystem":
            config["location"] = "filesystem"
            location = "filesystem"
        else:
            config["location"] = location

        if "aws" in location.lower():
            bucket_name = raw_input("%s. Bucket name: " % str(len(config) + 1))
            config["bucket_name"] = bucket_name
            region = raw_input(
                "%s. AWS Region (default: us-east-1): " % str(len(config) + 1))
            if len(region) == 0 or region == "us-east-1":
                config["s3_region"] = "us-east-1"
            else:
                config["s3_region"] = region
            access_key = raw_input(
                "%s. Access key for S3 bucket: " % str(len(config) + 1))
            config["access_key"] = access_key
            command = "aws configure set aws_access_key_id %s" % access_key
            subprocess.call(command.split(" "))
            secret_key = raw_input(
                "%s. Secret key for S3 bucket: " % str(len(config) + 1))
            config["secret_key"] = secret_key
            command = "aws configure set aws_secret_access_key %s" % secret_key
            subprocess.call(command.split(" "))

        # Set local path for project export/update
        path = raw_input("%s. Absolute path for exporting/updating projects? (default: %s) " % (
            str(len(config) + 1), os.getcwd()))
        if len(path) > 0 and path != os.getcwd() and path.startswith("/"):
            config["path"] = path
        else:
            print("Not an absolute path, setting default ({})".format(os.getcwd()))
            config["path"] = os.getcwd()

    reset_password = raw_input("Users receive password reset emails (default: true) ")
    if len(reset_password) != 0 and "false" in str(reset_password).lower().strip():
        config["reset_password"] = False
    else:
        config["reset_password"] = True

    force_random_password = raw_input("Should the users be created with a randomized password (default: false) ")
    if len(force_random_password) != 0 and "true" in str(force_random_password).lower().strip():
        config["force_random_password"] = True
    else:
        config["force_random_password"] = False

    config["number_of_threads"] = 2

    wrapper["config"] = config
    return wrapper


def config():
    config = generate_config()
    if not os.path.isdir("%s/data" % app_path):
        os.mkdir("%s/data" % app_path)
    if config["config"].get("path", None) is not None:
        if not os.path.isdir("%s/downloads" % config["config"]["path"]):
            os.mkdir("%s/downloads" % config["config"]["path"])
    with open("%s/data/config.json" % app_path, "w") as f:
        f.write(json.dumps(config, indent=4))
    time.sleep(1)
    print "## Congregate has been successfully configured"


def update_config(config_data):
    with open("%s/data/config.json" % app_path, "r") as f:
        data = json.load(f)
    data["config"] = json.loads(config_data)
    with open("%s/data/config.json" % app_path, "w") as f:
        json.dump(data, f, indent=4)
