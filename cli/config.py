import os
import subprocess
import json
try:
    from helpers.api import generate_get_request
except ImportError:
    from congregate.helpers.api import generate_get_request

app_path = os.getenv("CONGREGATE_PATH")

def config():
    config = {}

    print "##Configuring congregate"

    parent_instance_host = raw_input("%s. Host of parent instance (destination instance) " % str(len(config) + 1))
    config["parent_instance_host"] = parent_instance_host

    parent_instance_token = raw_input("%s. Access token to use for parent instance " % str(len(config) + 1))
    config["parent_instance_token"] = parent_instance_token

    config["parent_user_id"] = get_user(parent_instance_host, parent_instance_token)

    child_instance_host = raw_input("%s. Host of child instance (destination instance) " % str(len(config) + 1))
    config["child_instance_host"] = child_instance_host

    child_instance_token = raw_input("%s. Access token to use for child instance " % str(len(config) + 1))
    config["child_instance_token"] = child_instance_token

    parent_id = raw_input("Are you migrating the entire instance to a group? For example, migrating to our SaaS solution? (default: no)")
    if parent_id is None:
        pass
    else:
        parent_id = raw_input("%s. Please input the parent group ID (You can find this in the parent group -> settings -> general)" % str(len(config) + 1))
        config["parent_id"] = int(parent_id)

    location = raw_input("%s. Staging location type for exported projects? (default: filesystem) " % str(len(config) + 1))
    if location is None:
        config["location"] = "filesystem"
        location = "filesystem"
    else:
        config["location"] = location

    if location == "filesystem":
        path = raw_input("%s. Absolute path for exported projects? (default: %s) " % (str(len(config) + 1), os.getcwd()))
        if path is None:
            config["path"] = os.getcwd()
        else:
            config["path"] = path

    elif location.lower() == "aws":
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

    wrapper = {}
    wrapper["config"] = config

    with open("%s/data/config.json" % app_path, "w") as f:
        f.write(json.dumps(wrapper, indent=4))

    print "Congregate has been successfully configured"

def update_config(config_data):
    with open("%s/data/config.json" % app_path, "r") as f:
        data = json.load(f)
    data["config"] = json.loads(config_data)
    with open("%s/data/config.json" % app_path, "w") as f:
        json.dump(data, f, indent=4)

def get_user(parent_instance_host, parent_instance_token):
    response = generate_get_request(parent_instance_host, parent_instance_token, "user")
    return json.load(response)["id"]

if __name__ == "__main__":
    config()