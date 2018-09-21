import os
import subprocess
import json

app_path = os.getenv("CONGREGATE_PATH")

def config():
    config = {}

    print "##Configuring congregate"

    parent_instance_host = raw_input("1. Host of parent instance (destination instance) ")
    config["parent_instance_host"] = parent_instance_host

    parent_instance_token = raw_input("2. Access token to use for parent instance ")
    config["parent_instance_token"] = parent_instance_token

    child_instance_host = raw_input("3. Host of child instance (destination instance) ")
    config["child_instance_host"] = child_instance_host

    child_instance_token = raw_input("4. Access token to use for child instance ")
    config["child_instance_token"] = child_instance_token

    location = raw_input("5. Staging location type for exported projects? (default: filesystem) ")
    if location is None:
        config["location"] = "filesystem"
        location = "filesystem"
    else:
        config["location"] = location

    if location == "filesystem":
        path = raw_input("6. Absolute path for exported projects? (default: %s) " % os.getcwd())
        if path is None:
            config["path"] = os.getcwd()
        else:
            config["path"] = path
    elif location.lower() == "aws":
        bucket_name = raw_input("6. Bucket name: ")
        config["bucket_name"] = bucket_name
        access_key = raw_input("7. Access key for S3 bucket: ")
        config["access_key"] = access_key
        command = "aws configure set aws_access_key_id %s" % access_key
        subprocess.call(command.split(" "))
        secret_key = raw_input("8. Secret key for S3 bucket: ")
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

if __name__ == "__main__":
    config()