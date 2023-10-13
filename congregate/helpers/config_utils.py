import json
import sys
import os
import requests

from docker import from_env
from docker.errors import APIError, TLSParameterError

from congregate.helpers.utils import get_congregate_path
from congregate.helpers.configuration_validator import ConfigurationValidator

app_path = get_congregate_path()
config_path = f"{app_path}/data/congregate.conf"

def write_to_file(config):
    """
        Helper method to write congregate config to congregate.conf

        :param: data: (dict) config object
    """
    if not os.path.isdir(f"{app_path}/data"):
        os.mkdir(f"{app_path}/data")
        os.mkdir(f"{app_path}/data/logs")
        os.mkdir(f"{app_path}/data/results")
    if config.has_option("EXPORT", "filesystem_path") and config.get(
            "EXPORT", "filesystem_path"):
        down_dir = config.get("EXPORT", "filesystem_path")
        sub_dir = "downloads"
        if not os.path.isdir("{0}/{1}".format(down_dir, sub_dir)):
            print(
                f"Filesystem path {down_dir} sub-folder 'downloads' does not exist. Creating it...")
            f_path = os.path.join(down_dir, sub_dir)
            os.makedirs(f_path)
    with open(config_path, "w") as f:
        print(f"Writing configuration to file ({config_path})...")
        config.write(f)

def test_registries(token, registry, user):
    try:
        client = from_env()
        client.login(username=user.get("username"),
                     password=token, registry=registry)
    except (APIError, TLSParameterError) as err:
        print(
            f"Failed to login to docker registry {registry}, with error:\n{err}")
        sys.exit(os.EX_NOPERM)
    except Exception as e:
        print(
            f"Login attempt to docker registry {registry} failed, with error:\n{e}")
        sys.exit(os.EX_UNAVAILABLE)


def test_slack(url):
    try:
        json_data = json.dumps({"text": "Congregate Slack alerting test",
                                "username": "WebhookBot", "icon_emoji": ":ghost:"})
        resp = requests.post(url, data=json_data.encode('ascii'),
                             headers={'Content-Type': 'application/json'})
        if resp.status_code not in [200, 202]:
            raise Exception(resp)
    except Exception as em:
        print("EXCEPTION: " + str(em))
        sys.exit(os.EX_UNAVAILABLE)


def update_config(data):
    """
        Update function used by the congregate UI

        :param: data: (dict) Config data provided by user
        :return: No update message if config wasn't changed
    """
    config = ConfigurationValidator()
    config_obj = config.as_obj()
    x = 0
    y = 0

    # Flag to track config changes
    write_new_config = False
    options_list = [d.strip("{}").replace('"', '') for d in data.split(",")]

    # Loop over current config options, per section, and compare with UI input
    # fields
    for section in config_obj.sections():
        options = config_obj.items(section)
        y += len(options)
        for (k1, v1), k in zip(options, options_list[x:y]):
            k2 = k.split(":", 1)[0]
            v2 = k.split(":", 1)[1]

            # Set new option value in case of changes
            if k1 == k2 and v2 != v1:
                write_new_config = True
                print(
                    f"Updating config option {section}/{k1} from {v1} -> {v2}")
                config_obj.set(section, k1, v2)
        x += len(options)

    if write_new_config:
        write_to_file(config_obj)
    else:
        return ("No pending config changes")